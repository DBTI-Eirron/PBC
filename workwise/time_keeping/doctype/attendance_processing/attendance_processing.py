# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_schedule, get_holiday_list, get_leave_list, get_shift_map, get_card_within, 
get_attendance, get_defaults, get_ob_list, get_ot_list, get_ut_list, get_ext_list, get_sorted_card, get_suspension_map, get_suspension, insert_overtime)

class AttendanceProcessing(Document):
	def get_employees(self):
		employees = frappe.db.sql("""SELECT `name`, full_name, biometrics_id, company, location,is_attendance_base, no_hours FROM tabEmployee WHERE company = %(company)s {conditions}
			AND is_active = 1 ORDER BY `full_name` """.format(conditions=self.get_employee_conditions()),{ 
				"company": self.company,
				"employee": self.employee,
				"department": self.department,
				"location": self.location,
			}, as_dict=True)

		return employees

	def get_employee_conditions(self):
		conditions = []
		if self.employee:
			conditions.append("`name`=%(employee)s")
		if self.department:
			conditions.append("department=%(department)s")
		if self.location:
			conditions.append("location=%(location)s")

		return "and {}".format(" and ".join(conditions)) if conditions else ""

	def process_attendance(self):
		if not self.period:
			frappe.throw(_("Please Select Payroll Period"))
		
		employees = self.get_employees()
		ss_list = []

		if employees:
			pay_from, pay_to, approval_cutoff = frappe.db.get_value("Payroll Period", self.period, ["attendance_from", "attendance_to", "approval_cutoff"])
			for emp in employees:
				data = []
				pay_from, pay_to = frappe.db.get_value("Payroll Period", self.period, ["attendance_from", "attendance_to"])
				frappe.db.sql("""DELETE FROM `tabAttendance Register` WHERE employee = %s AND target_date >= %s AND target_date <= %s """,(emp.name, pay_from, pay_to), as_dict=1)
				frappe.db.sql("""DELETE FROM `tabOvertime` WHERE employee = %s AND target_date >= %s AND target_date <= %s """,(emp.name, pay_from, pay_to), as_dict=1)
				
				shift_map = get_shift_map()
				suspension_map = get_suspension_map(pay_from, pay_to)
				timecard_list = get_timecard_list(emp.biometrics_id, pay_from, pay_to + datetime.timedelta(days=1))
				schedule = get_schedule(emp.name, pay_from, pay_to)
				holidays = get_holiday_list(emp.company, emp.location, pay_from, pay_to)
				leaves = get_leave_list(emp.name, pay_from, pay_to, approval_cutoff, 0)
				ots = get_ot_list(emp.name, pay_from, pay_to, approval_cutoff, 0)
				obs = get_ob_list(emp.name, pay_from, pay_to, approval_cutoff, 0)
				uts = get_ut_list(emp.name, pay_from, pay_to, approval_cutoff, 0)
				ext = get_ext_list(emp.name, pay_from, pay_to, approval_cutoff, 0)

				for sched in schedule:
					entry = get_defaults(emp, sched, shift_map)
					cards_in, cards_out = get_card_within(entry.get('pre_shift'), entry.get('end_preshift'), entry.get('post_shift'), entry.get('end_postshift'), timecard_list)
					get_sorted_card(entry, cards_in, cards_out)
					get_suspension(emp, suspension_map, entry)
					get_attendance(entry, leaves, holidays, obs, ots, uts, ext)
					entry['break'] = self.convert_secs(entry['break'])
					entry['work'] = self.convert_secs(entry['work'])
					entry['late'] = self.convert_secs(entry['late'])
					entry['undertime'] = self.convert_secs(entry['undertime'])
					entry['overtime'] = self.convert_secs(entry['overtime'])
					entry['overtime_nd'] = self.convert_secs(entry['overtime_nd'])
					entry['overtime_ex'] = self.convert_secs(entry['overtime_ex'])
					entry['nightdiff'] = self.convert_secs(entry['nightdiff'])
					insert_overtime(entry)
					register = frappe.new_doc("Attendance Register")
					register.update(entry)
					register.insert()
						

				payslip_label = "Created for "+ cstr(emp.full_name) +""
				ss_list.append(payslip_label)
		else:
			frappe.throw(_("No Employee Found"))
		
		return self.create_log(ss_list)

	def create_log(self, ss_list):
		log = "<p>" + _("No Employee for the above selected criteria Attendance or Already Created") + "</p>"
		if ss_list:
			log = "<b>" + _("Attendance Registers Created") + "</b>\
			<br><br>%s" % '<br>'.join(self.format_as_links(ss_list))
		return log

	def format_as_links(self, ss_list):
		return ['<a href="#Form/Attendance Register/{0}">{0}</a>'.format(s) for s in ss_list]

	def convert_secs(self, secs):
		# Converts to HR
		con = (secs / 60) / 60
		return con