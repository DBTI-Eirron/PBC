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
from workwise.time_keeping.application_utils import ( grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, 
change_owner, get_levelled_approval, get_levelled_approval_rejection, clear_approval_history, validate_inactive_employee )

class OvertimeApplication(Document):
	def validate(self):
		validate_inactive_employee(self)
		clear_approval_history(self)
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
			frappe.throw(_("<b>Overtime Application: {0}</b><hr> From Date should be equal to Target Date").format(self.name))

		if new_from_date > new_to_date:
			frappe.throw(_("<b>Overtime Application: {0}</b><hr> From Date must be before To Date").format(self.name))

	def calculate_totals(self):
		self.validate_time_format()
		from_date = str(self.from_date) + ' ' + str(self.from_time)
		to_date = str(self.to_date) + ' ' + str(self.to_time)
		
		if self.break_hrs:
			total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")
			self.total_hrs = total_hrs - flt(self.break_hrs, 8)
		else:
			total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")
			self.total_hrs = total_hrs

	def get_autobreak_hrs(self):
		if self.is_new():
			if not self.amended_from:
				if not self.break_hrs:
					self.break_hrs = 0.00

		from_date = str(self.from_date) + ' ' + str(self.from_time)
		to_date = str(self.to_date) + ' ' + str(self.to_time)
		total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")

		schedule = get_schedule(self.employee, self.target_date, self.target_date)
		if schedule:
			shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0].work_shift), as_dict=True)
			if shifts:
				autobreak_setup = frappe.db.sql("""SELECT break_mins, from_hrs, to_hrs FROM `tabOvertime Auto Break Table` WHERE `parenttype` = "Work Shift" AND `parent` = %s """,(shifts[0].name), as_dict=True)
				if autobreak_setup:
					for a in autobreak_setup:
						if flt(a.from_hrs) <= flt(total_hrs) <= flt(a.to_hrs):
							self.break_hrs = flt(a.break_mins, 2)/60
							break
							
	def validate_overtime(self):
		schedule = get_schedule(self.employee, self.target_date, self.target_date)
		if schedule:
			shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0].work_shift), as_dict=True)
			if shifts:
				if shifts[0].min_ot_hrs > 0:
					if flt(self.total_hrs, 2) < flt(shifts[0].min_ot_hrs, 2):
						frappe.throw(_("<b>Overtime Application: {0}</b><hr> Minimum Overtime Hours Per Application is {1} Hours, Did not save").format(self.name, shifts[0].min_ot_hrs))
				
				if shifts[0].max_ot_hrs > 0:
					if flt(self.total_hrs, 2) > flt(shifts[0].max_ot_hrs, 2):
						frappe.throw(_("<b>Overtime Application: {0}</b><hr> Maximum Overtime Hours Per Application is {1} Hours, Did not save").format(self.name, shifts[0].max_ot_hrs))
				
				if shifts[0].max_ot_break > 0:
					if flt(self.break_hrs, 2) > flt(shifts[0].max_ot_break, 2):
						frappe.throw(_("<b>Overtime Application: {0}</b><hr> Maximum Overtime Break is {1} Hours, Did not save").format(self.name, shifts[0].max_ot_break))
				
				if shifts[0].allow_ot_in_shift < 1:
					if shifts[0].time_in <= shifts[0].time_out:
						shift_from = datetime.datetime.strptime(str(self.target_date) + ' ' + str(shifts[0].time_in), '%Y-%m-%d %H:%M:%S')
						shift_to = datetime.datetime.strptime(str(self.target_date) + ' ' + str(shifts[0].time_out), '%Y-%m-%d %H:%M:%S')
					else:
						shift_from = datetime.datetime.strptime(str(self.target_date) + ' ' + str(shifts[0].time_in), '%Y-%m-%d %H:%M:%S')
						shift_to = datetime.datetime.strptime(str(self.target_date) + ' ' + str(shifts[0].time_out), '%Y-%m-%d %H:%M:%S') + datetime.timedelta(days=1)

					cur_from = datetime.datetime.strptime(str(self.from_date) + ' ' + str(self.from_time), '%Y-%m-%d %H:%M:%S')
					cur_to = datetime.datetime.strptime(str(self.to_date) + ' ' + str(self.to_time), '%Y-%m-%d %H:%M:%S')
					
					if (shift_from < cur_from < shift_to or shift_from < cur_to < shift_to) or (shift_from == cur_from and cur_to == shift_to) or (cur_from < shift_from < cur_to or cur_from < shift_to < cur_to):
						emp_location = frappe.get_value("Employee", self.employee, "location")
						is_holiday = frappe.db.sql("""SELECT `name` FROM `tabHoliday` WHERE holiday_date = %s AND ((company = %s AND location = %s) OR company = %s) """, (getdate(self.target_date), self.company, emp_location, self.company), as_dict=True)
						if not is_holiday:
							frappe.throw(_("<b>Overtime Application: {0}</b><hr> Overtime Filing is not allowed within the Shift, Did not save").format(self.name))
				
				if shifts[0].max_ot_hrs_day > 0:
					total_max_ot_hrs = 0.0
					max_application = frappe.db.sql(""" SELECT `total_hrs` FROM `tabOvertime Application` WHERE `docstatus` = 1 AND `employee` = %s AND `target_date` = %s  """,(self.employee, self.target_date), as_dict=True)
					for max_app in max_application:
						total_max_ot_hrs += flt(max_app.total_hrs, 2)
					total_max_ot_hrs += flt(self.total_hrs, 2)
					if flt(total_max_ot_hrs, 2) > flt(shifts[0].max_ot_hrs_day, 2):
						frappe.throw(_("<b>Overtime Application: {0}</b><hr> Maximum overtime hours per day is {1} hours. You currently filed a total of {2} hours. \nDid not save").format(self.name, shifts[0].max_ot_hrs_day, total_max_ot_hrs))

	def validate_duplicate_ot_application(self):
		application = frappe.db.sql(""" SELECT `name`, to_date, to_time, from_date, from_time FROM `tabOvertime Application` WHERE `docstatus` = 1 AND `employee` = %s AND `target_date` = %s  """,(self.employee, self.target_date), as_dict=True)
		if application:
			for d in application:
				existing_ot_from = datetime.datetime.strptime(str(d.from_date) + ' ' + str(d.from_time), '%Y-%m-%d %H:%M:%S')
				existing_ot_to = datetime.datetime.strptime(str(d.to_date) + ' ' + str(d.to_time), '%Y-%m-%d %H:%M:%S')
				
				cur_from = datetime.datetime.strptime(str(self.from_date) + ' ' + str(self.from_time), '%Y-%m-%d %H:%M:%S')
				cur_to = datetime.datetime.strptime(str(self.to_date) + ' ' + str(self.to_time), '%Y-%m-%d %H:%M:%S')

				if existing_ot_from == cur_from and existing_ot_to == cur_to:
					frappe.throw(_("<b>Overtime Application: {0}</b><hr> Application already exists, {1}").format(self.name, d.name))
				if existing_ot_from < cur_from < existing_ot_to or existing_ot_from < cur_to < existing_ot_to:
					frappe.throw(_("<b>Overtime Application: {0}</b><hr> Application already exists, {1}").format(self.name, d.name))
				if cur_from < existing_ot_from < cur_to or cur_from < existing_ot_to < cur_to:
					frappe.throw(_("<b>Overtime Application: {0}</b><hr> Application already exists, {1}").format(self.name, d.name))