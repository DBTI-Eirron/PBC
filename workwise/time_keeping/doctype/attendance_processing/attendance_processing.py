# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import get_timecard_list, get_schedule, get_holiday_list, get_leave_list, get_shift_map, get_card_within, get_attendance

class AttendanceProcessing(Document):
	def get_employees(self):
		if self.employee:
			employees = frappe.db.sql("""SELECT `name` FROM tabEmployee WHERE company = %(company)s AND `name` = %(employee)s 
				AND on_hold = 0 AND is_active = 1 """,{ 
					"company": self.company,
					"employee": self.employee
				}, as_dict=True)
		else:
			employees = frappe.db.sql("""SELECT `name` FROM tabEmployee WHERE company = %(company)s 
				AND on_hold = 0 AND is_active = 1 """,{ 
					"company": self.company
				}, as_dict=True)

		return employees

	def process_attendance(self):
		if not self.payroll_period:
			frappe.throw(_("Please Select Payroll Period"))
		
		employees = self.get_employees()
		ss_list = []

		if employees:
			for emp in employees:
				data = []
				full_name, bio, company, worker_hrs, is_attendance_base = frappe.db.get_value("Employee", emp.name, ["full_name","biometrics_id", "company", "no_hours", "is_attendance_base"])
				worker_secs = (worker_hrs * 60) * 60
				pay_from, pay_to = frappe.db.get_value("Payroll Period", self.payroll_period, ["attendance_from", "attendance_to"])
				
				exist = frappe.db.sql("""SELECT `name` FROM `tabAttendance Register` WHERE employee = %s AND target_date >= %s AND target_date <= %s LIMIT 1""",(emp.name, pay_from, pay_to), as_dict=1)
				if exist:
					frappe.db.sql("""DELETE FROM `tabAttendance Register` WHERE employee = %s AND target_date >= %s AND target_date <= %s """,(emp.name, pay_from, pay_to), as_dict=1)

				shift_map = get_shift_map()
				timecard_list = get_timecard_list(bio, pay_from, pay_to + datetime.timedelta(days=1))
				schedule = get_schedule(emp.name, pay_from, pay_to)
				holidays = get_holiday_list(company, pay_from, pay_to)
				leaves = get_leave_list(emp.name, pay_from, pay_to)

				for sched in schedule:
					entry = {
						#employee settings
						"employee": emp.name,
						"employee_name": full_name,
						"worker_hrs": worker_hrs,
						"worker_secs": worker_secs,
						"is_attendance_base": is_attendance_base,
						#schedule settings
						"target_date": datetime.datetime.strftime(sched.datetime_in, '%Y-%m-%d'),
						"work_shift": sched.work_shift,
						"pre_shift": add_to_date(sched.datetime_in, hours= (0 - shift_map[sched.work_shift]['setup_preshift']) ),
						"post_shift": add_to_date(sched.datetime_out, hours=shift_map[sched.work_shift]['setup_postshift']),
						"time_in": sched.datetime_in,
						"time_out": sched.datetime_out,
						"break_start": sched.break_start,
						"break_end": sched.break_end,
						#shift policy
						"work_hours": sched.work_hours,
						"break_mins": sched.break_mins,
						"grace": shift_map[sched.work_shift]['grace_period'],
						"b_grace": shift_map[sched.work_shift]['b_grace_period'],
						"is_flexible": shift_map[sched.work_shift]['is_flexible'],		
						"is_restday": shift_map[sched.work_shift]['is_restday'],
						"ignore_late": shift_map[sched.work_shift]['ignore_late'],
						#general policy
						"approved_ot_only": 1,
						"is_processed": 1,
						#timecard data
						"card_in": "",
						"card_out": "",			
						"break_out": "",
						"break_in": "",
						#basic attendance
						"work": 0.0,
						"late": 0.0,
						"break": 0.0,
						"undertime": 0.0,
						"nightdiff": 0.0,
						"is_absent": 0,
						"is_halfday": 0,
						#applications
						#OT
						"overtime": 0.0,
						"linked_ot": "",
						#LEAVE
						"is_leave": 0,
						"leave_name": "",
						"is_lwop": 0,
						"linked_leave": "",
						#NIGHTDIFF
						"nd_start": sched.nd_start,
						"nd_end": sched.nd_end,
						#OB
						"is_ob": 0,
						"ob": 0.0,
						"linked_ob": "",
						#holiday
						"is_holiday": 0,
						"is_sp_holiday": 0,
						"holiday_name": "",
						"linked_holiday": "",
						"has_issue": 0
					}
					
					#ATTENDANCE
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


					get_attendance(entry, leaves, holidays)

					entry['break'] = self.convert_secs(entry['break'])
					entry['work'] = self.convert_secs(entry['work'])
					entry['late'] = self.convert_secs(entry['late'])
					entry['undertime'] = self.convert_secs(entry['undertime'])
					entry['overtime'] = self.convert_secs(entry['overtime'])
					register = frappe.new_doc("Attendance Register")
					register.update(entry)
					register.insert()
				payslip_label = "Created for "+ cstr(full_name) +""
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