# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, cstr, add_to_date, add_days
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.payroll.payroll_utils import get_rates, get_overtime_map
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_schedule, get_holiday_list, get_leave_list, get_shift_map, get_card_within, 
get_attendance, get_defaults, get_ob_list, get_ot_list, get_ut_list, get_ext_list, get_sorted_card, get_suspension_map, get_suspension)

class AdjustmentProcessing(Document):
	def get_employees(self):
		if self.employee:
			employees = frappe.db.sql("""SELECT `name`, full_name, location, company, total_yr_days, rate_type, rate, payroll_schedule, min_take_home, cost_center, no_hours, 
				sss_mode, sss_manual, sss_freq, phic_mode, phic_manual, phic_freq, hdmf_mode, hdmf_manual, hdmf_freq, whtax_mode, 
				whtax_manual, whtax_freq, is_attendance_base, ignore_late, on_hold
					FROM tabEmployee
					WHERE company = %(company)s
				AND `name` = %(employee)s
				AND payroll_schedule = %(pay_sched)s 
				AND is_active = 1 
				AND sensitivity IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
				ORDER BY last_name, first_name""",{ 
					"company": self.company,
					"pay_sched": self.schedule,
					"employee": self.employee
				}, as_dict=True)
		else:
			employees = frappe.db.sql("""SELECT `name`, full_name, location, company, total_yr_days, rate_type, rate, payroll_schedule, min_take_home, cost_center, no_hours, 
				sss_mode, sss_manual, sss_freq, phic_mode, phic_manual, phic_freq, hdmf_mode, hdmf_manual, hdmf_freq, whtax_mode, 
				whtax_manual, whtax_freq, is_attendance_base, ignore_late, on_hold
					FROM tabEmployee
					WHERE company = %(company)s
				AND payroll_schedule = %(pay_sched)s 
				AND is_active = 1 
				AND sensitivity IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
				ORDER BY last_name, first_name""",{ 
					"company": self.company,
					"pay_sched": self.schedule
				}, as_dict=True)

		return employees

	def validate_period(self):
		period_stats = frappe.db.get_value("Payroll Period", self.period, "status")
		if period_stats == "Closed":
			frappe.throw(_("Selected Period is Already Closed"))

		if not self.schedule and not self.payroll_date:
			frappe.throw(_("Fill up Mandatory Fields"))

	def get_previous_period(self):
		before = frappe.db.sql_list(""" SELECT `name` FROM `tabPayroll Period` WHERE company = %s 
			AND `schedule` = %s AND payroll_date < %s ORDER BY payroll_date DESC LIMIT 1 """,(self.company, self.schedule, self.payroll_date ))
		previous_period = before[0] if before else ""
		
		return previous_period
 
	def process_adjustment(self):
		self.validate_period()
		ss_list = []
		prev_period = self.get_previous_period()
		prev_attendance_from, prev_attendance_to, prev_approval_cutoff = frappe.db.get_value("Payroll Period", prev_period, ["attendance_from", "attendance_to", "approval_cutoff"])
		employees = self.get_employees()
		ot_map = get_overtime_map()

		for d in employees:
			if self.validate_for_adjustment(d.name, prev_attendance_from, prev_attendance_to, prev_approval_cutoff):
				frappe.db.sql("""DELETE FROM `tabAdjustment Register` WHERE employee = %s 
					AND payroll_period = %s  """,(d.name, self.period), as_dict=1)
				
				adjustment_sched = self.get_adjustment_schedule(d, prev_attendance_from, prev_attendance_to, prev_approval_cutoff)
				original_sched = frappe.db.sql("""SELECT * FROM `tabAttendance Register` WHERE employee = %s AND target_date >= %s AND target_date <= %s 
					ORDER BY target_date """,(d.name, add_days(prev_attendance_from, -1), prev_attendance_to), as_dict=1)

				adjustment = self.get_attendance_result(d, adjustment_sched, prev_attendance_from, prev_attendance_to, ot_map)
				original = self.get_attendance_result(d, original_sched, prev_attendance_from, prev_attendance_to, ot_map)
				
				register = {
					"employee": d.name,
					"employee_name": d.full_name,
					"payroll_period": self.period,
					"absent": adjustment.get('ab') - original.get('ab'),
					"unpaid_holiday": adjustment.get('uho') - original.get('uho'),
					"overtime": adjustment.get('ot') - original.get('ot'),
					"nightdiff": adjustment.get('nd') - original.get('nd'),
					"late": adjustment.get('lt') - original.get('lt'),
					"undertime":  adjustment.get('ut') - original.get('ut')
				}
				
				adjr = frappe.new_doc("Adjustment Register")
				adjr.update(register)
				adjr.insert()

		return self.create_log(ss_list)

	def delete_adjustment(self):
		self.validate_period()
		frappe.db.sql("""DELETE FROM `tabAdjustment Register` WHERE payroll_period = %s  """, (self.period), as_dict=1)

	def validate_for_adjustment(self, employee, attendance_from, attendance_to, approval_cutoff):
		result = 0
		leave_list = frappe.db.sql(""" SELECT L.`name` FROM `tabLeave Application Table` LA
			INNER JOIN `tabLeave Application` L ON L.`name` = LA.parent WHERE L.employee = %s AND LA.leave_date >= %s AND LA.leave_date <= %s AND L.approved_on >= %s AND L.docstatus = 1 
			ORDER BY LA.leave_date ASC """, (employee, attendance_from, attendance_to, approval_cutoff), as_dict=1)

		ob_list = frappe.db.sql("""SELECT OBA.`name` FROM `tabOfficial Business Application Table` OBAT
			INNER JOIN `tabOfficial Business Application` OBA  ON OBAT.parent = OBA.`name`
			WHERE OBA.employee = %s AND OBA.workflow_state = 'Approved' AND OBAT.target_date >= %s 
			AND OBAT.target_date <= %s AND OBAT.is_excluded = 0 AND approved_on >= %s """, (employee, attendance_from, attendance_to, approval_cutoff), as_dict=1)	

		ot_list = frappe.db.sql("""SELECT `name` FROM `tabOvertime Application` 
			WHERE workflow_state = 'Approved' AND employee = %s AND target_date >= %s 
			AND target_date <= %s AND approved_on >= %s """, (employee, attendance_from, attendance_to, approval_cutoff), as_dict=1)

		ut_list = frappe.db.sql("""SELECT `name` FROM `tabUndertime Application` 
			WHERE workflow_state = 'Approved' AND employee = %s AND from_date >= %s 
			AND from_date <= %s AND approved_on >= %s """, (employee,  attendance_from, attendance_to, approval_cutoff), as_dict=1)

		cto_list = frappe.db.sql("""SELECT `name`, use_fromtime, use_totime,  use_date FROM `tabCompensatory Time Off` 
			WHERE workflow_state = 'Approved' AND employee = %s AND use_date >= %s AND use_date <= %s
			AND `type` = 'Use' AND approved_on >= %s """, (employee,  attendance_from, attendance_to, approval_cutoff), as_dict=1)

		ext_apps = frappe.db.sql("""SELECT `name`, `date`, from_time, to_time, `type` FROM `tabExcuse Tardiness Application` 
			WHERE workflow_state = 'Approved' AND employee = %s AND `date` >= %s 
			AND `date` <= %s AND approved_on >= %s """, (employee,  attendance_from, attendance_to, approval_cutoff), as_dict=1)		

		if leave_list or ob_list or ot_list or ut_list or cto_list or ext_apps:
			result = 1

		return result

	def get_adjustment_schedule(self, emp, pay_from, pay_to, approval_cutoff):
		adjustment_schedule = []
		shift_map = get_shift_map()
		suspension_map = get_suspension_map(pay_from, pay_to)
		timecard_list = get_timecard_list(emp.biometrics_id, pay_from, pay_to + datetime.timedelta(days=1))	
		holidays = get_holiday_list(emp.company, emp.location, pay_from, pay_to)
		schedule = get_schedule(emp.name, pay_from, pay_to)
		leaves = get_leave_list(emp.name, pay_from, pay_to, approval_cutoff, 1)
		ots = get_ot_list(emp.name, pay_from, pay_to, approval_cutoff, 1)
		obs = get_ob_list(emp.name, pay_from, pay_to, approval_cutoff, 1)
		uts = get_ut_list(emp.name, pay_from, pay_to, approval_cutoff, 1)
		ext = get_ext_list(emp.name, pay_from, pay_to, approval_cutoff, 1)

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
			entry['nightdiff'] = self.convert_secs(entry['nightdiff'])
			adjustment_schedule.append(entry)
		
		return adjustment_schedule

	def get_attendance_result(self, emp, attendance, attendance_from, attendance_to, ot_map):
		rates = get_rates(emp)
		attendance_result = { "ab": 0.0, "uho": 0.0, "ot": 0.0, "nd": 0.0, "lt": 0.0, "ut": 0.0 }
		lwop_uho = frappe.db.get_single_value('Payroll Settings', 'hd_lwop_as_uho')
		if emp.get('is_attendance_base') > 0:
			late, overtime, undertime, absent, nightdiff, work_days, absent_days, unpaid_holiday, prev_lwop, prev_absent, is_uho = 0, 0, 0, 0, 0, 0, 0, 0, 0 ,0, 0

			overtime_list = frappe.db.sql("""SELECT employee, target_date, ot_code, hrs, linked_ot FROM `tabOvertime` 
				WHERE employee = %s AND target_date >= %s AND target_date <= %s ORDER BY target_date """,(emp.get('name'), attendance_from, attendance_to), as_dict=1)
			
			for ot in overtime_list:
				if ot.ot_code in ot_map:
					overtime += flt( ot.hrs, 8) * rates.get('hourly_rate') * (ot_map[ot.get('ot_code')]['rate'] / 100)
				else:
					overtime += flt( ot.hrs, 8) * rates.get('hourly_rate')

			for at in attendance:
				if at.get('target_date') == add_days(attendance_from, -1):
					if at.get('is_absent') or at.get('is_lwop'):
						is_uho = 1
						if lwop_uho == 1:
							if (at.get('lv_status') == 2 or at.get('lv_status') == 3) or at.get('is_halfday'):
								is_uho = 0
								if at.get('is_absent'):
									is_uho = 1
				else: 
					if (emp.get("rate_type") == "Daily Rate" and at.get('is_holiday') == 1 and at.get('is_absent') != 1):
						work_days += 0
					elif not at.get('is_restday'):
						work_days += 1

					if at.get('late')> 0:
						late += flt(at.get('late'), 8) * flt(rates.get('hourly_rate'), 8)
					
					if at.get('undertime') > 0:
						undertime += flt(at.get('undertime'), 8) * flt(rates.get('hourly_rate'), 8)

					if at.get('nightdiff'):
						nightdiff += at.get('nightdiff') * 0.10 * rates.get('hourly_rate')

					if ( at.get('is_absent') == 1 or at.get('is_lwop') == 1 ) and not at.get('is_holiday'):
						if at.get('is_lwop') == 1 and at.get('lv_status') > 1:
							absent += ( at.get('work_hours') / 2 ) * flt(rates.get('hourly_rate'), 8)
							absent_days += 0.5
						else:
							absent += ( at.get('work_hours') / 2 ) * flt(rates.get('hourly_rate'), 8) if at.get('is_halfday') == 1 else ( at.get('work_hours') ) * flt(rates.get('hourly_rate'), 8)
							absent_days += 0.5 if at.get('is_halfday') == 1 else 1

					if at.get('is_holiday') == 1 and is_uho == 1 and not at.get('is_ob'):
						unpaid_holiday += at.get('work_hours') * flt(rates.get('hourly_rate'), 8)
						if header['uho_ab_days'] == 1:
							absent_days += 1

					#check if this attendance is lwop or absent for next attendance
					if is_uho == 1:
						#if present
						if at.get('work') and not at.get('at.is_lwop') and not at.get('at.absent') and not at.get('at.is_restday'):
							is_uho = 0

						if at.get('lv_status') == 1 and not at.get('is_lwop'):
							is_uho = 0

						if at.get('is_ob'):
							is_uho = 0

						if lwop_uho == 1:
							if ( at.get('lv_status') == 2 or at.get('lv_status == 3') ) or at.get('is_halfday'):
								is_uho = 0
								if at.get('is_absent') and at.get('is_lwop'):
									is_uho = 1
						else:
							if ( at.get('lv_status') == 2 or at.get('lv_status == 3') )  or at.get('is_halfday'):
								if at.get('is_absent'):
									is_uho = 0

					else:
						is_uho = 0
						if (at.get('is_absent') or at.get('is_lwop') ) and not at.get('is_ob'):
							is_uho = 1

							if lwop_uho == 1:
								if (at.get('lv_status') == 2 or at.get('lv_status') == 3) or at.get('is_halfday'):
									is_uho = 0
									if at.get('is_absent'):
										is_uho = 1

			#Daily rate should have no absent
			if emp.get("rate_type") == "Daily Rate":
				absent = 0
			if emp.get('ignore_late'):
				late = 0
				
			attendance_result.update({ "ab": flt(absent, 8), "uho": flt(unpaid_holiday, 8), "ot": flt(overtime, 8), "nd": flt(nightdiff, 8), "lt": flt(late, 8), "ut":flt(undertime, 8) })

			return attendance_result

	def create_log(self, ss_list):
		log = "<p>" + _("Adjustment Entries Created") + "</p>"
		return log

	def convert_secs(self, secs):
		# Converts to HR
		con = (secs / 60) / 60
		return con

