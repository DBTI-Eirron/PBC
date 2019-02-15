# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.utils import cint, flt, getdate, cstr, nowdate 
from frappe.model.document import Document
from workwise.time_keeping.attendance_utils import get_schedule
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs, sub_date, chk_time_format, timediff_hrs, timediff_mins, str_datetime
from workwise.time_keeping.application_utils import grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, change_owner, get_levelled_approval, get_levelled_approval_rejection

class OvertimeApplication(Document):
	def validate(self):
		grant_head_subordinate_access(self)
		self.validate_time_format()
		self.update_target_date()
		self.get_autobreak_hrs()
		self.validate_date()
		self.calculate_totals()
		change_owner(self)
		self.get_recipients()
		self.validate_overtime()
		self.validate_duplicate_ot_application()

	def on_submit(self):
		validate_approve_own_application(self)
		get_approver_and_date(self)

	def before_update_after_submit(self):
		get_levelled_approval(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)

	def validate_time_format(self):
		time_fds = ['from_time', 'to_time']
		for fd in time_fds:
			chk_time_format(str(self.get(fd)), "%H:%M:%S")

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

	def update_target_date(self):
		target_date = datetime.datetime.strptime(str(self.from_date) + ' ' + str(self.from_time), '%Y-%m-%d %H:%M:%S').date()
		if self.is_previous:
			self.target_date = target_date - datetime.timedelta(days=1)
		else:
			self.target_date = target_date

	def validate_date(self):
		from_date = datetime.datetime.strptime(str(self.from_date) + ' ' + str(self.from_time), '%Y-%m-%d %H:%M:%S').date()
		target_date = self.target_date
		
		new_from_date = datetime.datetime.strptime(str(self.from_date) + ' ' + str(self.from_time), '%Y-%m-%d %H:%M:%S').date()
		new_to_date = datetime.datetime.strptime(str(self.to_date) + ' ' + str(self.to_time), '%Y-%m-%d %H:%M:%S').date()

		if target_date != from_date and not self.is_previous:
			frappe.throw(_("From Date should be equal to Target Date"))

		if new_from_date > new_to_date:
			frappe.throw(_("From Date must be before To Date"))

	def calculate_totals(self):
		self.validate_time_format()
		from_date = str(self.from_date) + ' ' + str(self.from_time)
		to_date = str(self.to_date) + ' ' + str(self.to_time)
		
		if from_date <= to_date:
			total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")
			self.total_hrs = total_hrs - flt(self.break_hrs, 8)
		else:
			if self.break_hrs:
				total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")
				self.total_hrs = total_hrs - flt(self.break_hrs, 8)
			else:
				total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")
				self.total_hrs = total_hrs

	def get_autobreak_hrs(self):
		schedule = get_schedule(self.employee, self.target_date, self.target_date)
		if schedule:
			shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0].work_shift), as_dict=True)
			if shifts:
				autobreak_setup = frappe.db.sql("""SELECT break_mins, from_hrs, to_hrs FROM `tabOvertime Auto Break Table` WHERE `parenttype` = "Work Shift" AND `parent` = %s """,(shifts[0].name), as_dict=True)
				if autobreak_setup:
					for a in autobreak_setup:
						if a.from_hrs <= self.total_hrs <= a.to_hrs:
							self.break_hrs = flt(a.break_mins, 2)/60

	def validate_overtime(self):
		schedule = get_schedule(self.employee, self.target_date, self.target_date)
		if schedule:
			shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0].work_shift), as_dict=True)
			if shifts:
				if shifts[0].min_ot_hrs > 0:
					if flt(self.total_hrs, 2) < flt(shifts[0].min_ot_hrs, 2):
						frappe.throw(_("Minimum Overtime Hours is {0} Hours, Did not save").format(shifts[0].min_ot_hrs))
				if shifts[0].max_ot_hrs > 0:
					if flt(self.total_hrs, 2) > flt(shifts[0].max_ot_hrs, 2):
						frappe.throw(_("Maximum Overtime Hours is {0} Hours, Did not save").format(shifts[0].max_ot_hrs))
				if shifts[0].max_ot_break > 0:
					if flt(self.break_hrs, 2) > flt(shifts[0].max_ot_break, 2):
						frappe.throw(_("Maximum Overtime Break is {0} Hours, Did not save").format(shifts[0].max_ot_break))

		#Removed from timekeeping settings but still waiting for code removal confirmation
		#ot_req_break = frappe.db.get_single_value('Timekeeping Settings', 'ot_req_break')
		#if ot_req_break:
		#	if flt(self.total_hrs, 2) > flt(ot_req_break, 2) and flt(self.break_hrs, 	2) < 1:
		#		frappe.throw(_("Total Overtime hours is greater than {0} Break Time is required").format(ot_req_break))	

	def validate_duplicate_ot_application(self):
		application = frappe.db.sql(""" SELECT `name`, to_date, to_time, from_date, from_time FROM `tabOvertime Application` WHERE `docstatus` = 1 AND `employee` = %s AND `target_date` = %s  """,(self.employee, self.target_date), as_dict=True)
		if application:
			for d in application:
				existing_ot_from = datetime.datetime.strptime(str(d.from_date) + ' ' + str(d.from_time), '%Y-%m-%d %H:%M:%S')
				existing_ot_to = datetime.datetime.strptime(str(d.to_date) + ' ' + str(d.to_time), '%Y-%m-%d %H:%M:%S')
				
				cur_from = datetime.datetime.strptime(str(self.from_date) + ' ' + str(self.from_time), '%Y-%m-%d %H:%M:%S')
				cur_to = datetime.datetime.strptime(str(self.to_date) + ' ' + str(self.to_time), '%Y-%m-%d %H:%M:%S')

				if existing_ot_from <= cur_from <= existing_ot_to or existing_ot_from <= cur_to <= existing_ot_to:
					frappe.throw(_("Application already exists, {0}").format(d.name))