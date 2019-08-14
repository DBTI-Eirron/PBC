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
get_attendance, get_defaults, get_ob_list, get_ot_list, 
get_ut_list, get_ext_list, get_cto_list, get_sorted_card, get_wss_list, insert_overtime,init_employee_map,complete_sched,change_sched,get_template_map)

class AttendanceProcessing(Document):
	def get_employees(self):
		employees = frappe.db.sql("""SELECT `name`, full_name, biometrics_id, company, location, is_attendance_base, no_hours, rate_type, default_schedule FROM tabEmployee WHERE company = %(company)s 
			AND payroll_schedule = %(schedule)s {conditions}
			AND is_active = 1 ORDER BY `full_name` """.format(conditions=self.get_employee_conditions()),{ 
				"company": self.company,
				"employee": self.employee,
				"schedule": self.schedule,
				"department": self.department,
				"location": self.location,
				"period_group": self.period_group,
			}, as_dict=True)

		return employees

	def get_employee_conditions(self):
		strict_period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')
		conditions = []
		if self.employee:
			conditions.append("`name`=%(employee)s")
		
		if self.department:
			conditions.append("department=%(department)s")
		
		if self.location:
			conditions.append("location=%(location)s")

		if strict_period_group:
			conditions.append("period_group=%(period_group)s")

		return "and {}".format(" and ".join(conditions)) if conditions else ""

	def process_attendance(self):
		strict_period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')
		if not self.period:
			frappe.throw(_("Please Select Payroll Period"))
		
		if strict_period_group and not self.period_group:
			frappe.throw(_("Period Group is required for Payroll Period {0}").format(self.period))

		employees = self.get_employees()
		ss_list = 0

		if employees:
			pay_from, pay_to, approval_cutoff = frappe.db.get_value("Payroll Period", self.period, ["attendance_from", "attendance_to", "approval_cutoff"])
			employee_list = self.convert_to_list(employees)
			data = []
			ot_list = []
			reg_list = []

			if self.employee:
				employee = self.employee
			else:
				employee = None

			frappe.db.sql("""DELETE FROM `tabAttendance Register` WHERE target_date >= %s AND target_date <= %s and employee IN %s """,(pay_from, pay_to,employee_list), as_dict=1)
			frappe.db.sql("""DELETE FROM `tabOvertime` WHERE target_date >= %s AND target_date <= %s AND employee IN %s """,(pay_from, pay_to,employee_list), as_dict=1)
			template_map = get_template_map()
			shift_map = get_shift_map()
			emp_map = init_employee_map(employees, employee, self.company, pay_from, pay_to, approval_cutoff, 0)
			for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
				ss_list += 1
				complete_sched(emp_dict, pay_from, pay_to, template_map)
				change_sched(emp_dict, emp_dict['schedules'], emp_dict.get('csa'))
				for sched in emp_dict['schedules']:
					entry = get_defaults(emp_dict.get('employee_details'), sched, shift_map, emp_dict.get('overrides'))
					cards_in, cards_out = get_card_within(entry.get('pre_shift'), entry.get('end_preshift'), 
						entry.get('post_shift'), entry.get('end_postshift'), emp_dict.get('timecards'), emp_dict.get('dtrp'))
					get_sorted_card(entry, cards_in, cards_out)
					get_attendance(entry, emp_dict.get('overrides'), emp_dict.get('lvs'), emp_dict.get('hls'), emp_dict.get('obs'), 
						emp_dict.get('ots'), emp_dict.get('uts'), emp_dict.get('ext'), emp_dict.get('cto'), emp_dict.get('wss'), emp_dict.get('dtrp'))
					
					entry['break'] = self.convert_secs(entry['break'])
					entry['work'] = self.convert_secs(entry['work'])
					entry['late'] = self.convert_secs(entry['late'])
					entry['undertime'] = self.convert_secs(entry['undertime'])
					entry['overtime'] = self.convert_secs(entry['overtime'])
					entry['overtime_nd'] = self.convert_secs(entry['overtime_nd'])
					entry['overtime_ex'] = self.convert_secs(entry['overtime_ex'])
					entry['nightdiff'] = self.convert_secs(entry['nightdiff'])
					entry['cto'] = self.convert_secs(entry['cto'])
					ot_list.extend(entry.get('ot_list'))
					insert_overtime(entry)
					reg_list.append(entry)
				payslip_label = "Created for "+ cstr(emp_dict.get('employee_name')) +""

			for ot in ot_list:
				otdoc = frappe.new_doc("Overtime")
				otdoc.update({
					"employee": ot.get('employee'),
					"target_date": ot.get('target_date'),
					"ot_code": ot.get('ot_code'),	
					"hrs": ot.get('ot_hrs'),
					"linked_ot": ot.get('linked_ot'),
				})
				otdoc.flags.ignore_mandatory = True
				otdoc.flags.ignore_permissions = True
				otdoc.insert()				

			for reg in reg_list:
				register = frappe.new_doc("Attendance Register")
				register.update(reg)
				register.flags.ignore_mandatory = True
				register.flags.ignore_permissions = True
				register.insert()
		else:
			frappe.throw(_("No Employee Found"))
		
		return self.create_log(ss_list)

	def create_log(self, ss_list):
		log = "<p>" + _("No Employee for the above selected criteria Attendance or Already Created") + "</p>"
		if ss_list > 0:
			log = "<b>Attendance Registers Created for"+cstr(ss_list)+" Employees</b>"
		return log

	def format_as_links(self, ss_list):
		return ['<a href="#Form/Attendance Register/{0}">{0}</a>'.format(s) for s in ss_list]

	def convert_secs(self, secs):
		# Converts to HR
		con = (secs / 60) / 60
		return con

	def convert_to_list(self, dic):
		data = []
		for d in dic:
			data.append(d.name)
		return data