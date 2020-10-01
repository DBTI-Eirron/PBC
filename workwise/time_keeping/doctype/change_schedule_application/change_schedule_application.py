# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document
from workwise.time_keeping.attendance_utils import get_schedule
from workwise.time_keeping.application_utils import ( grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, change_owner, get_levelled_approval, 
	get_levelled_approval_rejection, clear_approval_history, validate_inactive_employee, get_approver_email_list, get_cancelled_by_and_date, validate_cutoff_approval_date, validate_approver_userperm, get_employee_details )

class ChangeScheduleApplication(Document):
	def on_submit(self):
		#emp_app = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
		#if emp_app < 1:
		#	self.change_sched()
		validate_approve_own_application(self)
		change_owner(self)
		self.get_recipients()
		get_approver_and_date(self)
		get_approver_email_list(self, 'on_submit')
		#validate_approver_userperm(self)
		validate_cutoff_approval_date(self)

	#def on_update_after_submit(self):
	#	emp_app = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
	#	if emp_app > 0:
	#		if self.workflow_state == "Approved":
	#			self.change_sched()

	def before_update_after_submit(self):
		get_levelled_approval(self)
		get_approver_email_list(self, 'before_update_after_submit')
		#validate_approver_userperm(self)
		validate_cutoff_approval_date(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		self.revert_change_sched()
		get_cancelled_by_and_date(self)

	def validate(self):
		get_employee_details(self)
		validate_inactive_employee(self)
		clear_approval_history(self)
		grant_head_subordinate_access(self)
		self.validate_dates()
		self.validate_existing_application()

	def validate_dates(self):
		unique_ent = []
		unique_entries = []

		for i in self.change_list:
			if str(i.target_date) not in unique_ent:
				unique_ent.append(str(i.target_date));

				entries = {
				    "target_date": i.target_date,
			        "current_shift": i.current_shift,
			        "new_shift": i.new_shift,
			        "time_in": i.time_in,
			        "time_out":i.time_out,
			    }
				unique_entries.append(entries);

		self.set('change_list', [])
		for ue in unique_entries:
			row = self.append('change_list', {})
			row.update(ue)
		
	def validate_existing_application(self):
		for i in self.change_list:
			if i.current_shift == i.new_shift:
				frappe.throw(_("<b>Change Schedule Application: {0}</b><hr> New Shift should not be equal to Current Shift").format(self.name))
			is_existing = frappe.db.sql(""" SELECT CA.`name` FROM `tabChange Schedule Application` CA INNER JOIN `tabChange Schedule Application Table` CT ON CA.`name`=CT.`parent` 
				WHERE CA.docstatus = 1 AND CA.workflow_state = 'Approved' AND CA.`employee` = %s AND CT.`target_date` = %s 
				AND CT.`current_shift` = %s AND CT.`new_shift` = %s LIMIT 1 """, (self.employee, i.target_date, i.current_shift, i.new_shift), as_dict=True)
			if is_existing:
				frappe.throw(_("<b>Change Schedule Application: {0}</b><hr> Application already exists. {1}").format(self.name, is_existing[0].name))

	def change_sched(self):
		for i in self.change_list:
			old_shift = ""
			work_shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(i.new_shift), as_dict=True)
			
			exist = frappe.db.sql("""SELECT `name` FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (self.employee, i.target_date), as_dict=True)
			if exist:
				frappe.db.sql("""DELETE FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (self.employee, i.target_date), as_dict=True)
				frappe.db.commit()
				
			old_shift = frappe.db.sql_list("""SELECT `work_shift` FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s LIMIT 1""", (self.employee, i.target_date))
			target_date = getdate(i.target_date)

			for ws in work_shift:
				work_sched = frappe.new_doc("Work Schedule")
				work_sched.update({
					"employee": self.employee,
					"company": self.company,
					"target_date": target_date,
					"work_shift": ws.name,
					"shift_type": ws.work_shift_type,
					"work_hours": ws.work_hours,
					"break_mins": ws.break_mins,
					"datetime_in": self.get_date(target_date, ws.time_in, ws.time_out, ws.work_shift_type, 0), 
					"datetime_out": self.get_date(target_date, ws.time_in, ws.time_out, ws.work_shift_type, 1),			
					"break_start": self.get_date(target_date, ws.break_start, ws.break_end, ws.work_shift_type, 0),
					"break_end": self.get_date(target_date, ws.break_start, ws.break_end, ws.work_shift_type, 1),
					"nd_start": self.get_date(target_date, ws.nd_start, ws.time_out, ws.nd_end, 0),
					"nd_end": self.get_date(target_date, ws.nd_start, ws.time_out, ws.nd_end, 1),
				})
				if work_sched.insert():
					frappe.db.commit()
					if old_shift:
						i.current_shift = old_shift
				else:
					frappe.throw(_("<b>Change Schedule Application: {0}</b><hr> Changing Failed").format(self.name))

	def revert_change_sched(self):
		for i in self.change_list:
			old_shift = ""
			work_shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(i.current_shift), as_dict=True)
			
			exist = frappe.db.sql("""SELECT `name` FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (self.employee, i.target_date), as_dict=True)
			if exist:
				frappe.db.sql("""DELETE FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (self.employee, i.target_date), as_dict=True)
				frappe.db.commit()
			
			old_shift = frappe.db.sql_list("""SELECT `work_shift` FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s LIMIT 1""", (self.employee, i.target_date))
			target_date = getdate(i.target_date)

			for ws in work_shift:
				work_sched = frappe.new_doc("Work Schedule")
				work_sched.update({
					"employee": self.employee,
					"company": self.company,
					"target_date": target_date,
					"work_shift": ws.name,
					"shift_type": ws.work_shift_type,
					"work_hours": ws.work_hours,
					"break_mins": ws.break_mins,
					"datetime_in": self.get_date(target_date, ws.time_in, ws.time_out, ws.work_shift_type, 0), 
					"datetime_out": self.get_date(target_date, ws.time_in, ws.time_out, ws.work_shift_type, 1),			
					"break_start": self.get_date(target_date, ws.break_start, ws.break_end, ws.work_shift_type, 0),
					"break_end": self.get_date(target_date, ws.break_start, ws.break_end, ws.work_shift_type, 1),
					"nd_start": self.get_date(target_date, ws.nd_start, ws.time_out, ws.nd_end, 0),
					"nd_end": self.get_date(target_date, ws.nd_start, ws.time_out, ws.nd_end, 1),
				})
				if work_sched.insert():
					frappe.db.commit()
					if old_shift:
						i.current_shift = old_shift
				else:
					frappe.throw(_("<b>Change Schedule Application: {0}</b><hr> Changing Failed").format(self.name))

	def get_date(self, date, start, end, type, is_end):
		if is_end == 1:
			if self.delta_to_time(start) > self.delta_to_time(end):
				dt = (datetime.datetime.combine( date, self.delta_to_time(end) ) + datetime.timedelta(days=1) ).strftime('%Y-%m-%d %H:%M:%S')
			else:
				dt = datetime.datetime.combine( date, self.delta_to_time(end) ).strftime('%Y-%m-%d %H:%M:%S') 
		else:
			dt = datetime.datetime.combine( date, self.delta_to_time(start) ).strftime('%Y-%m-%d %H:%M:%S') 
	
		return dt

	def delta_to_time(self, delta_obj):
		return (datetime.datetime.min + delta_obj).time()
			
	def get_recipients(self):
		recipients = []
		managers = frappe.db.sql("""SELECT ES.employee, E.user_id FROM `tabEmployee Subordinates` ES 
			INNER JOIN `tabSubordinates` S ON S.parent = ES.name
			LEFT JOIN `tabEmployee` E ON ES.employee = E.name
			WHERE S.subordinate = %s """,(self.employee), as_dict=True)
		
		for d in managers:
			if d.user_id:
				recipients.append(d.user_id)

		if recipients:
			send_to = ', '.join(str(x) for x in recipients)
			self.managers_list = send_to

	def get_dates(self):
		entries = []
		dates = []
		change_list = []

		start = datetime.datetime.strptime(str(self.from_date), '%Y-%m-%d')
		end = datetime.datetime.strptime(str(self.to_date), '%Y-%m-%d')
		step = datetime.timedelta(days=1)
		
		while start <= end:
		    dates.append(start.date());
		    start += step
		    
		for i in dates:
		    info = {
			    "target_date": i,
		        "current_shift": "",
		        "new_shift": "",
		        "time_in": "00:00:00",
		        "time_out": "00:00:00"
		    }
		    
		    change_list.append(info);
		
		entries = sorted(list(change_list), 
			key=lambda k: k['target_date'])		    

		self.set('change_list', [])
		
		for d in entries:
			row = self.append('change_list', {})
			row.update(d)

		self.get_shift()

	def get_shift(self):
		for d in self.change_list:
			if d.target_date:
				schedule = get_schedule(self.employee, d.target_date, d.target_date)
				for x in schedule:
					d.current_shift = x['work_shift']

