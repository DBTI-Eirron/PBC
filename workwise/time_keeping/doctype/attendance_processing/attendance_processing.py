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
get_attendance, get_defaults, get_ob_list, get_ot_list, get_ut_list, get_ext_list)

class AttendanceProcessing(Document):
	def get_employees(self):
		employees = frappe.db.sql("""SELECT `name`, full_name, biometrics_id, company, location,is_attendance_base, no_hours FROM tabEmployee WHERE company = %(company)s {conditions}
			AND on_hold = 0 AND is_active = 1 ORDER BY `full_name` """.format(conditions=self.get_employee_conditions()),{ 
				"company": self.company,
				"employee": self.employee
			}, as_dict=True)

		return employees

	def get_employee_conditions(self):
		conditions = []
		if self.employee:
			conditions.append("`name`=%(employee)s")
		return "and {}".format(" and ".join(conditions)) if conditions else ""

	def process_attendance(self):
		if not self.period:
			frappe.throw(_("Please Select Payroll Period"))
		
		employees = self.get_employees()
		ss_list = []

		if employees:
			for emp in employees:
				data = []
				pay_from, pay_to = frappe.db.get_value("Payroll Period", self.period, ["attendance_from", "attendance_to"])
				frappe.db.sql("""DELETE FROM `tabAttendance Register` WHERE employee = %s AND target_date >= %s AND target_date <= %s """,(emp.name, pay_from, pay_to), as_dict=1)
				
				shift_map = get_shift_map()
				timecard_list = get_timecard_list(emp.biometrics_id, pay_from, pay_to + datetime.timedelta(days=1))
				schedule = get_schedule(emp.name, pay_from, pay_to)
				holidays = get_holiday_list(emp.company, emp.location, pay_from, pay_to)
				leaves = get_leave_list(emp.name, pay_from, pay_to)
				ots = get_ot_list(emp.name, pay_from, pay_to)
				obs = get_ob_list(emp.name, pay_from, pay_to)
				uts = get_ut_list(emp.name, pay_from, pay_to)
				ext = get_ext_list(emp.name, pay_from, pay_to)

				for sched in schedule:
					entry = get_defaults(emp, sched, shift_map)
					card_list = get_card_within(entry.get('pre_shift'), entry.get('post_shift'), timecard_list)		
					sorted_card_list = sorted(card_list, key=lambda k: k['card_datetime'])
					for card in sorted_card_list:
						if card['card_type'] == 0:
							if entry['card_in'] == "":
								entry['card_in'] = card['card_datetime']
						elif card['card_type'] == 1:
							entry['card_out'] = card['card_datetime']
						elif card['card_type'] == 2:
							if entry['break_out'] == "":
								entry['break_out'] = card['card_datetime']
						elif card['card_type'] == 3:
							entry['break_in'] = card['card_datetime']

					get_attendance(entry, leaves, holidays, obs, ots, uts, ext)
					entry['break'] = self.convert_secs(entry['break'])
					entry['work'] = self.convert_secs(entry['work'])
					entry['late'] = self.convert_secs(entry['late'])
					entry['undertime'] = self.convert_secs(entry['undertime'])
					entry['overtime'] = self.convert_secs(entry['overtime'])
					entry['nightdiff'] = self.convert_secs(entry['nightdiff'])
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