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
get_attendance, get_defaults, get_ob_list, get_ot_list, 
get_ut_list, get_ext_list, get_cto_list, get_sorted_card, get_wss_list, insert_overtime,init_employee_map,complete_sched,get_template_map)

class AdjustmentProcessing(Document):
	def get_employees(self):
		employees = frappe.db.sql("""SELECT `name`, full_name, location, company, total_yr_days, rate_type, rate, payroll_schedule, 
			min_take_home, mth_percentage, cost_center, no_hours, 
			sss_mode, sss_manual, sss_freq, phic_mode, phic_manual, phic_freq, hdmf_mode, hdmf_manual, hdmf_freq, whtax_mode, 
			whtax_manual, whtax_freq, is_attendance_base, ignore_late, ignore_ut, on_hold, sensitivity, default_schedule, biometrics_id
				FROM tabEmployee
			WHERE company = %(company)s
			AND payroll_schedule = %(pay_sched)s 
			AND is_active = 1
			{conditions}
			ORDER BY last_name, first_name""".format( conditions=self.get_conditions() ),
			({ 
				"company": self.company,
				"pay_sched": self.schedule,
				"employee": self.employee,
				"department": self.department,
				"location": self.location,
				"period_group": self.period_group,
			}), as_dict=True)

		return employees

	def get_conditions(self):
		conditions = []
		strict_period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')
		if self.employee:
			conditions.append("`name`=%(employee)s")

		if self.department:
			conditions.append("department=%(department)s")

		if self.location:
			conditions.append("location=%(location)s")

		if strict_period_group:
			conditions.append("period_group=%(period_group)s")
		
		if frappe.session.user != "Administrator":
			conditions.append(_("sensitivity IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

		return "and {}".format(" and ".join(conditions)) if conditions else ""

	def validate_period(self):
		p_stats, p_date, p_comp = frappe.db.get_value("Payroll Period", self.period,  ["status", "payroll_date", "company"])
		tgt_stats, tgt_date, tgt_comp = frappe.db.get_value("Payroll Period", self.target_period, ["status", "payroll_date", "company"])

		if not self.schedule and not self.payroll_date:
			frappe.throw(_("Fill up Mandatory Fields"))

		if tgt_date <= p_date:
			frappe.throw(_("Target Period, Payroll Date should be higher"))

		if tgt_comp != p_comp:
			frappe.throw(_("Target Period and Payroll Period Should have the same Company"))

	def get_adjusted(self, emp_adj_map, ot_adj_list, employees):
		data = []

		#Validate Period
		self.validate_period()
		if not self.period:
			frappe.throw(_("Please Select Payroll Period"))
		
		#Validate Period Group
		strict_period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')
		if strict_period_group and not self.period_group:
			frappe.throw(_("Period Group is required for Payroll Period {0}").format(self.period))
		
		pay_from, pay_to, approval_cutoff = frappe.db.get_value("Payroll Period", self.period, ["attendance_from", "attendance_to", "approval_cutoff"])
		employee_list = self.convert_to_list(employees)
		template_map = get_template_map()
		shift_map = get_shift_map()
		emp_map = init_employee_map(employees, None, self.company, pay_from, pay_to, approval_cutoff, 1)
		for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
			complete_sched(emp_dict, pay_from, pay_to, template_map)
			for sched in emp_dict['schedules']:
				entry = get_defaults(emp_dict.get('employee_details'), sched, shift_map, emp_dict.get('overrides'))
				cards_in, cards_out = get_card_within(entry.get('pre_shift'), entry.get('end_preshift'), 
					entry.get('post_shift'), entry.get('end_postshift'), emp_dict.get('timecards'))
				get_sorted_card(entry, cards_in, cards_out)
				get_attendance(entry, emp_dict.get('lvs'), emp_dict.get('hls'), emp_dict.get('obs'), 
					emp_dict.get('ots'), emp_dict.get('uts'), emp_dict.get('ext'), emp_dict.get('cto'), emp_dict.get('wss'))
				
				entry['break'] = self.convert_secs(entry['break'])
				entry['work'] = self.convert_secs(entry['work'])
				entry['late'] = self.convert_secs(entry['late'])
				entry['undertime'] = self.convert_secs(entry['undertime'])
				entry['overtime'] = self.convert_secs(entry['overtime'])
				entry['overtime_nd'] = self.convert_secs(entry['overtime_nd'])
				entry['overtime_ex'] = self.convert_secs(entry['overtime_ex'])
				entry['nightdiff'] = self.convert_secs(entry['nightdiff'])
				entry['cto'] = self.convert_secs(entry['cto'])
				data.append(entry)

		for d in data:
			if d['employee'] in emp_adj_map:
				emp_adj_map[d['employee']].adjustment.append(d)
				emp_adj_map[d['employee']].adjustment_ot.extend(d['ot_list'])
								
	def get_processed(self, emp_map):
		attendance = frappe.db.sql("""SELECT * FROM `tabAttendance Register` WHERE target_date >= %s AND target_date <= %s 
			ORDER BY target_date """,(add_days(self.attendance_from, -1), self.attendance_to), as_dict=1)

		for d in attendance:
			if d.employee in emp_map:
				emp_map[d.employee].processed.append(d)

	def get_processed_ot(self, emp_map):
		overtime = frappe.db.sql("""SELECT employee, target_date, ot_code, hrs, linked_ot FROM `tabOvertime` 
			WHERE target_date >= %s AND target_date <= %s ORDER BY target_date """,(getdate(self.attendance_from), getdate(self.attendance_to)), as_dict=1)
		
		for d in overtime:
			if d.employee in emp_map:
				emp_map[d.employee].processed_ot.append(d)
 
	def process_adjustment(self):
		emp_map = frappe._dict()
		employees = self.get_employees()
		ot_adj_list = []
		ss_list = []
		ot_map = get_overtime_map()
		for emp in employees:
			emp_map.setdefault(emp.name, frappe._dict({
					"employee": emp.name,
					"employee_name": emp.full_name,
					"employee_details": emp,
					"processed": [],
					"processed_ot": [],
					"adjustment": [],
					"adjustment_ot": [],
				})
			)

		self.get_adjusted(emp_map, ot_adj_list, employees)
		self.get_processed(emp_map)
		self.get_processed_ot(emp_map)

		for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
			frappe.db.sql("""DELETE FROM `tabAdjustment Register` WHERE employee = %s AND payroll_period = %s  """,(emp_dict['employee'], self.period), as_dict=1)
			adjustment = self.get_attendance_result(emp_dict['employee_details'], emp_dict['adjustment'], self.attendance_from, self.attendance_to, emp_dict['adjustment_ot'], ot_map)
			processed = self.get_attendance_result(emp_dict['employee_details'], emp_dict['processed'], self.attendance_from, self.attendance_to, emp_dict['processed_ot'], ot_map)

			reg = {
				"employee": emp_dict['employee'],
				"employee_name": emp_dict['employee_name'],
				"company": self.company,
				"payroll_period": self.period,
				"target_period": self.target_period,
				"absent": adjustment.get('ab') - processed.get('ab'),
				"unpaid_holiday": adjustment.get('uho') - processed.get('uho'),
				"overtime": adjustment.get('ot') - processed.get('ot'),
				"nightdiff": adjustment.get('nd') - processed.get('nd'),
				"late": adjustment.get('lt') - processed.get('lt'),
				"undertime":  adjustment.get('ut') - processed.get('ut')
			}

			if reg.get('absent') or reg.get('unpaid_holiday') or reg.get('overtime') or reg.get('nightdiff') or reg.get('late') or reg.get('undertime'):
				adjr = frappe.new_doc("Adjustment Register")
				adjr.update(reg)
				adjr.insert()
				ss_list.append(" " + emp_dict['employee_name'] +"")

		return self.create_log(ss_list)

	def delete_adjustment(self):
		self.validate_period()
		frappe.db.sql("""DELETE FROM `tabAdjustment Register` WHERE payroll_period = %s  """, (self.period), as_dict=1)

	def get_attendance_result(self, emp, attendance, attendance_from, attendance_to, ot_list, ot_map):
		rates = get_rates(emp)
		attendance_result = { "ab": 0.0, "uho": 0.0, "ot": 0.0, "nd": 0.0, "lt": 0.0, "ut": 0.0 }
		lwop_uho = frappe.db.get_single_value('Payroll Settings', 'hd_lwop_as_uho')
		uho_ab_days = frappe.db.get_single_value('Payroll Settings', 'uho_ab_days')
		hd_no_uho = frappe.db.get_single_value('Payroll Settings', 'hd_no_uho')
		if emp.get('is_attendance_base') > 0:
			late, overtime, undertime, absent, nightdiff, work_days, absent_days, unpaid_holiday, prev_lwop, prev_absent, is_uho, cto, cto_days = 0, 0, 0, 0, 0, 0, 0, 0, 0 ,0, 0, 0, 0
			
			for ot in ot_list:
				if ot.get('ot_code') in ot_map:
					overtime += flt( ot.get('ot_hrs'), 8) * rates.get('hourly_rate') * (ot_map[ot.get('ot_code')]['rate'] / 100)
				else:
					overtime += flt( ot.get('ot_hrs'), 8) * rates.get('hourly_rate')		
				
			for at in attendance:
				if getdate(at.get('target_date')) == getdate(add_days(attendance_from, -1)):
					if at.get('is_absent') or at.get('is_lwop'):
						is_uho = 0
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

					if at.get('is_holiday') == 1 and is_uho == 1 and not at.get('is_ob')  and not at.get('is_restday'):
						unpaid_holiday += at.get('work_hours') * flt(rates.get('hourly_rate'), 8)
						if uho_ab_days == 1:
							absent_days += 1

					if at.get('cto'):
						max_cto = 0
						max_cto += at.get('undertime')
						max_cto += at.get('late')
						if ( at.get('is_absent') == 1 or at.get('is_lwop') == 1 ) and not at.get('is_holiday'):
							if at.get('is_lwop') == 1 and at.get('lv_status') > 1:
								max_cto += ( at.get('work_hours') / 2 )
							else:
								max_cto += ( at.get('work_hours') / 2 ) if at.get('is_halfday') == 1 else at.get('work_hours')

						if max_cto < at.get('cto'):
							cto += ( max_cto ) * flt(rates.get('hourly_rate'), 8)
						else:
							cto += ( at.get('cto') ) * flt(rates.get('hourly_rate'), 8)

						if at.get('is_absent') == 1:
							if at.get('is_halfday') == 1 and max_cto >= (at.get('work_hours') / 2):
								cto_days += 0.5
							elif max_cto >= at.get('work_hours'):
								cto_days += 1

					if at.get('is_holiday') == 1 and is_uho == 1 and (not at.get('is_ob')) and not at.get('is_restday'):
						if emp.get("rate_type") == "Daily Rate" and at.get('is_absent'):
							#if Daily Rate is Absent on Holiday should not have Unpaid Holiday
							unpaid_holiday += 0
						else:
							unpaid_holiday += at.get('work_hours') * flt(rates.get('hourly_rate'), 8)
							if uho_ab_days == 1:
								absent_days += 1

					#check if this attendance is lwop or absent for next attendance
					if is_uho == 1:
						#if present
						if at.get('work') and (not at.get('at.is_lwop')) and (not at.get('at.absent')) and (not at.get('at.is_restday')):
							is_uho = 0

						#if Halfday next day will not be UHO
						if hd_no_uho and at.get('is_halfday'):
							is_uho = 0

						#if Proper Leave next day is not UHO
						if at.get('lv_status') == 1 and not at.get('is_lwop'):
							is_uho = 0

						#if proper OB next day is not UHO
						if at.get('is_ob'):
							is_uho = 0

						#UHO if Absent and leave withoutpay
						if at.get('is_absent') and at.get('is_lwop'):
							is_uho = 1

						#Not UHO if halfday and halfday leave
						if (at.get('lv_status') == 2 or at.get('lv_status') == 3) and at.get('is_halfday'):
							is_uho = 0
							if lwop_uho == 1 and at.get('is_lwop'):
								is_uho = 1
						
						#strictly No UHO if CTO can cover absent work hours
						if at.get('is_absent') and at.get('work_hours') <= at.get('cto'):
							is_uho = 0	

					else:
						is_uho = 0
						if (at.get('is_absent') or at.get('is_lwop')) and not at.get('is_ob'):
							is_uho = 1

							if lwop_uho == 1:
								if (at.get('lv_status') == 2 or at.get('lv_status') == 3) and at.get('is_halfday'):
									is_uho = 0
									if at.get('is_absent'):
										is_uho = 1
						
						#If Halfday is LWOP but not absent
						if lwop_uho == 1:
							if (at.get('lv_status') == 2 or at.get('lv_status') == 3) and at.get('is_lwop') and (not at.get('is_absent')):
								is_uho = 0
						
						#strictly No UHO if CTO can cover absent work hours
						if at.get('is_absent') and at.get('work_hours') <= at.get('cto'):
							is_uho = 0	

						#if Halfday next day will not be UHO
						if hd_no_uho and at.get('is_halfday'):
							is_uho = 0

					if emp.get("rate_type") == "Daily Rate":
						#if daily rate, holiday is considered paid
						if at.get('is_holiday') and not at.get('is_restday'):
							work_days += 1
							if at.get('is_absent') and at.get('is_sp_holiday') and header.get('uho_ab_spnw'):
								work_days -= 1
								unpaid_holiday += at.get('work_hours') * flt(rates.get('hourly_rate'), 8)

			#Daily rate should have no absent
			if emp.get("rate_type") == "Daily Rate":
				absent = 0
			
			if emp.get('ignore_late'):
				late = 0

			if emp.get('ignore_ut'):
				undertime = 0

			if frappe.db.get_single_value('Timekeeping Settings', 'ignore_nd'):
				nightdiff = 0

			attendance_result.update({ "ab": flt(absent, 8), "uho": flt(unpaid_holiday, 8), "ot": flt(overtime, 8), "nd": flt(nightdiff, 8), "lt": flt(late, 8), "ut":flt(undertime, 8) })
		
		return attendance_result

	def create_log(self, ss_list):
		log = "<p>" + _("No Employee for the above selected criteria Adjustment or Already Created") + "</p>"
		if ss_list:
			log = "<b>" + _("Adjustment Registers Created") + "</b>\
			<br><br>%s" % '<br>'.join(self.format_as_links(ss_list))
		return log

	def format_as_links(self, ss_list):
		return ['{0}'.format(s) for s in ss_list]

	def convert_secs(self, secs):
		# Converts to HR
		con = (secs / 60) / 60
		return con

	def convert_to_list(self, dic):
		data = []
		for d in dic:
			data.append(d.name)
		return data

