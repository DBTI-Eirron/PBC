# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, cstr, add_to_date, add_days
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.payroll.payroll_utils import get_rates, get_overtime_map, get_ot_class_map, get_rateclass_map
from workwise.time_keeping.application_utils import validate_inactive_employee
from workwise.payroll.payroll_attendance_utils import get_absent_days
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_schedule, get_holiday_list, get_leave_list, get_shift_map, get_card_within, 
get_attendance, get_defaults, get_ob_list, get_ot_list, get_ut_list, get_ext_list, get_cto_list, get_sorted_card, get_wss_list, insert_overtime, 
init_employee_map, complete_sched, get_template_map, change_sched, processed_def_sched, get_multi_breaks)

class AdjustmentProcessing(Document):
	def get_employees(self):
		employees = frappe.db.sql("""SELECT TE.`name`, TE.full_name, TE.location, TE.company, TE.total_yr_days, TE.rate_type, TE.rate, TE.rate_class,
			TE.payroll_schedule, TE.min_take_home, TE.mth_percentage, TE.cost_center, TE.no_hours, TE.sss_mode, TE.sss_manual, TE.sss_freq, 
			TE.phic_mode, TE.phic_manual, TE.phic_freq, TE.hdmf_mode, TE.hdmf_manual, TE.hdmf_freq, TE.whtax_mode, TE.whtax_manual, TE.whtax_freq, 
			TE.is_attendance_base, TE.ignore_late, TE.ignore_ut, TE.on_hold, TE.sensitivity, TE.default_schedule, TE.biometrics_id, TE.date_hired
			FROM `tabEmployee` TE LEFT JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name`
			WHERE TE.company = %(company)s
			AND TE.payroll_schedule = %(pay_sched)s 
			AND TE.is_active = 1
			AND TE.date_hired <= %(attendance_to)s
			{conditions}
			ORDER BY TE.last_name, TE.first_name""".format( conditions=self.get_conditions() ),
			({ 
				"company": self.company,
				"pay_sched": self.schedule,
				"employee": self.employee,
				"department": self.department,
				"location": self.location,
				"period_group": self.period_group,
				"attendance_to": getdate(self.attendance_to),
			}), as_dict=True)

		return employees

	def get_conditions(self):
		conditions = []
		strict_period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')
		if self.employee:
			conditions.append("TE.`name`=%(employee)s")

		if self.department:
			lft, rgt = frappe.db.get_value("Department", self.department, ["lft", "rgt"])
			conditions.append(_("( DEPT.`lft` BETWEEN '{0}' AND '{1}' )").format(lft, rgt))

		if self.location:
			conditions.append("TE.location=%(location)s")

		if strict_period_group:
			conditions.append("TE.period_group=%(period_group)s")
		
		if frappe.session.user != "Administrator":
			conditions.append(_("TE.sensitivity IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

		return "AND {}".format(" AND ".join(conditions)) if conditions else ""

	def validate_period(self):
		p_stats, p_date, p_comp = frappe.db.get_value("Payroll Period", self.period,  ["status", "payroll_date", "company"])
		tgt_stats, tgt_date, tgt_comp = frappe.db.get_value("Payroll Period", self.target_period, ["status", "payroll_date", "company"])

		if p_comp != self.company:
			frappe.throw(_("Selected Payroll Period does not belong to company"))

		if p_stats == "Open":
			frappe.throw(_("Selected Payroll Period is still Open"))

		if tgt_comp != self.company:
			frappe.throw(_("Selected Target Period does not belong to company"))

		if tgt_stats == "Closed":
			frappe.throw(_("Selected Target Period is already Closed"))

		if not self.schedule and not self.payroll_date:
			frappe.throw(_("Fill up Mandatory Fields"))

		if tgt_date <= p_date:
			frappe.throw(_("Target Period, Payroll Date should be higher"))

		if tgt_comp != p_comp:
			frappe.throw(_("Target Period and Payroll Period Should have the same Company"))

	def get_adjusted(self, emp_adj_map, ot_adj_list, employees):
		data = []
		#Validate Inactive Employee
		if self.employee:
			validate_inactive_employee(self)
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
			complete_sched(emp_dict, pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1), template_map)
			change_sched(emp_dict, emp_dict['schedules'], emp_dict.get('csa'))
			processed_def_sched(emp, pay_from, pay_to, emp_dict['schedules'])
			for sched in emp_dict['schedules']:
				if sched['target_date'] not in [pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1)]:
					entry = get_defaults(emp_dict.get('employee_details'), sched, shift_map, emp_dict.get('overrides'))
					cards_in, cards_out = get_card_within(entry, sched['target_date'], emp_dict['timelogs_map'], emp_dict['schedules'], shift_map, entry.get('pre_shift'), entry.get('end_preshift'), 
						entry.get('post_shift'), entry.get('end_postshift'), emp_dict.get('timecards'), emp_dict.get('dtrp'), emp_dict.get('tla'))
					get_sorted_card(entry, cards_in, cards_out, emp_dict['timelogs_map'])
					get_multi_breaks(entry, cards_in, cards_out)
					get_attendance(entry, emp_dict.get('overrides'),emp_dict.get('lvs'), emp_dict.get('hls'), emp_dict.get('obs'), 
						emp_dict.get('ots'), emp_dict.get('uts'), emp_dict.get('ext'), emp_dict.get('cto'), emp_dict.get('wss'), emp_dict.get('dtrp'), emp_dict.get('tla'))
	
					entry['break'] = self.convert_secs(entry['break'])
					entry['work'] = self.convert_secs(entry['work'])
					entry['late'] = self.convert_secs(entry['late'])
					entry['undertime'] = self.convert_secs(entry['undertime'])
					entry['overtime'] = self.convert_secs(entry['overtime'])
					entry['overtime_nd'] = self.convert_secs(entry['overtime_nd'])
					entry['overtime_ex'] = self.convert_secs(entry['overtime_ex'])
					entry['nightdiff'] = self.convert_secs(entry['nightdiff'])
					entry['cto'] = self.convert_secs(entry['cto'])
					if frappe.db.get_single_value('Payroll Settings', 'nd_rate_class'):
						entry['earlynightdiff'] = self.convert_secs(entry['earlynightdiff'])
						entry['latenightdiff'] = self.convert_secs(entry['latenightdiff'])
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
		overtime = frappe.db.sql("""SELECT employee, target_date, ot_code, hrs, linked_ot, early_nd, late_nd FROM `tabOvertime` 
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
		employees = self.validate_adjustment_period(employees)
		for emp in employees:
			emp_map.setdefault(emp.name, frappe._dict({
					"employee": emp.name,
					"employee_name": emp.full_name,
					"employee_details": emp,
					"rate_type": emp.rate_type,
					"processed": [],
					"processed_ot": [],
					"adjustment": [],
					"adjustment_ot": [],
				})
			)

		self.get_adjusted(emp_map, ot_adj_list, employees)
		self.get_processed(emp_map)
		self.get_processed_ot(emp_map)

		sys_settings = {
			"lwop_uho": frappe.db.get_single_value('Payroll Settings', 'hd_lwop_as_uho'),
			"ex_uho_spnw": frappe.db.get_single_value('Payroll Settings', 'ex_uho_spnw'),
			"uho_ab_days": frappe.db.get_single_value('Payroll Settings', 'uho_ab_days'),
			"hd_no_uho": frappe.db.get_single_value('Payroll Settings', 'hd_no_uho'),
			"uho_ab_spnw": frappe.db.get_single_value('Payroll Settings', 'uho_ab_spnw'),
			"ab_regho": frappe.db.get_single_value('Timekeeping Settings', 'ab_regho'),
			"mo_abho": frappe.db.get_single_value('Timekeeping Settings', 'mo_abho'),
			"disable_pdhord": frappe.db.get_single_value('Payroll Settings', 'disable_pdhord'),
			"ignore_uho": frappe.db.get_single_value('Payroll Settings', 'ignore_uho'),
			"ignore_nd": frappe.db.get_single_value('Timekeeping Settings', 'ignore_nd'),
			"dis_dho_tran": frappe.db.get_single_value('Payroll Settings', 'disable_dho_tran'),
			"nd_rate_class": frappe.db.get_single_value('Payroll Settings', 'nd_rate_class'),
			"ot_rate_class": frappe.db.get_single_value('Payroll Settings', 'ot_rate_class'),
		}
		if self.exclude_processed_adjustment:
			past_adjustment = frappe.db.sql("""SELECT * FROM `tabAdjustment Register` 
				WHERE payroll_period = %s AND target_period != %s """,(self.period, self.target_period), as_dict=1)
		for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
			if not self.exclude_processed_adjustment:
				frappe.db.sql("""DELETE FROM `tabAdjustment Register` WHERE employee = %s AND payroll_period = %s  """,(emp_dict['employee'], self.period), as_dict=1)
				frappe.db.sql("""DELETE FROM `tabAdjustment Register Adjusted` WHERE employee = %s AND payroll_period = %s  """,(emp_dict['employee'], self.period), as_dict=1)
				frappe.db.sql("""DELETE FROM `tabAdjustment Register Processed` WHERE employee = %s AND payroll_period = %s  """,(emp_dict['employee'], self.period), as_dict=1)
				frappe.db.sql("""DELETE FROM `tabOvertime Adjustment Register` WHERE employee = %s AND previous_payroll_period = %s  """,(emp_dict['employee'], self.period), as_dict=1)
			if self.exclude_processed_adjustment:
				frappe.db.sql("""DELETE FROM `tabAdjustment Register` WHERE employee = %s AND payroll_period = %s AND target_period = %s  """,(emp_dict['employee'], self.period, self.target_period), as_dict=1)
				frappe.db.sql("""DELETE FROM `tabAdjustment Register Adjusted` WHERE employee = %s AND payroll_period = %s AND target_period = %s  """,(emp_dict['employee'], self.period, self.target_period), as_dict=1)
				frappe.db.sql("""DELETE FROM `tabAdjustment Register Processed` WHERE employee = %s AND payroll_period = %s AND target_period = %s  """,(emp_dict['employee'], self.period, self.target_period), as_dict=1)
				frappe.db.sql("""DELETE FROM `tabOvertime Adjustment Register` WHERE employee = %s AND previous_payroll_period = %s AND current_payroll_period = %s  """,(emp_dict['employee'], self.period, self.target_period), as_dict=1)	
			adjustment, adjustment_time = self.get_attendance_result(emp_dict['employee_details'], emp_dict['adjustment'], self.attendance_from, self.attendance_to, emp_dict['adjustment_ot'], ot_map, sys_settings, "adjustment")
			processed, processed_time = self.get_attendance_result(emp_dict['employee_details'], emp_dict['processed'], self.attendance_from, self.attendance_to, emp_dict['processed_ot'], ot_map, sys_settings, "processed")
			rates = get_rates(emp_dict['employee_details'])

			if self.exclude_processed_adjustment:
				for p in past_adjustment:
					if emp_dict['employee_details']['name'] == p.employee:
						adjustment_time['work']  = adjustment_time['work'] - p['adjusted_work_hrs']
						adjustment_time['absent'] = adjustment_time['absent'] - p['adjusted_absent_hrs']
						adjustment_time['undertime'] = adjustment_time['undertime'] - p['adjusted_undertime_hrs']
						adjustment_time['nd'] = adjustment_time['nd'] - p['adjusted_nd_hrs']
						adjustment_time['late'] = adjustment_time['late'] - p['adjusted_late_hrs']
						adjustment_time['overtime'] = adjustment_time['overtime'] - p['adjusted_overtime_hrs']
						adjustment_time['cto'] = adjustment_time['cto'] - p['adjusted_cto_hrs']
						adjustment_time['uho'] = adjustment_time['uho'] - p['adjusted_uho_hrs']
						adjustment['absent_days'] = adjustment.get('absent_days') - p['absent']
						adjustment['AT'] = adjustment.get('AT') - p['absent']
						adjustment['UHO'] = adjustment['UHO'] - p['unpaid_holiday']
						adjustment['OT'] = adjustment['OT'] - p['overtime']
						adjustment['ND'] = adjustment['ND'] - p['nightdiff']
						adjustment['LT'] = adjustment['LT'] - p['late']
						adjustment['UT'] = adjustment['UT'] - p['undertime']
						adjustment['CTO'] = adjustment['CTO'] - p['compensatory']
						for l in list(adjustment['adjusted_leave_application_links']):
							if str(l) in str(p['adjusted_leave_application_links']):
								adjustment['adjusted_leave_application_links'].remove(l)
		
						for o in list(adjustment['adjusted_overtime_application_links']):
							if str(o) in str(p['adjusted_overtime_application_links']):
								adjustment['adjusted_overtime_application_links'].remove(o)

						for ob in list(adjustment['adjusted_official_business_application_links']):
							if str(ob) in str(p['adjusted_official_business_application_links']):
								adjustment['adjusted_official_business_application_links'].remove(ob)

						for e in list(adjustment['adjusted_excuse_tardiness_application_links']):
							if str(e) in str(p['adjusted_excuse_tardiness_application_links']):
								adjustment['adjusted_excuse_tardiness_application_links'].remove(e)

						for u in list(adjustment['adjusted_undertime_application_links']):
							if str(u) in str(p['adjusted_undertime_application_links']):
								adjustment['adjusted_undertime_application_links'].remove(u)

						for d in list(adjustment['adjusted_dtr_problem_application_links']):
							if str(d) in adjustment.get('adjusted_dtr_problem_application_links'):
								adjustment['adjusted_dtr_problem_application_links'].remove(d)

						for c in list(adjustment['adjusted_compensatory_time_off_links']):
							if str(c) in adjustment.get('adjusted_compensatory_time_off_links'):
								adjustment['adjusted_compensatory_time_off_links'].remove(c)

						for t in list(adjustment['adjusted_timelogs_application_links']):
							if str(t) in adjustment.get('adjusted_timelogs_application_links'):
								adjustment['adjusted_timelogs_application_links'].remove(t)


			reg = {
				"employee": emp_dict['employee'],
				"employee_name": emp_dict['employee_name'],
				"company": self.company,
				"payroll_period": self.period,
				"target_period": self.target_period,
				"absent": adjustment.get('AT') - processed.get('AT'),
				"unpaid_holiday": adjustment.get('UHO') - processed.get('UHO'),
				"overtime": adjustment.get('OT') - processed.get('OT'),
				"nightdiff": adjustment.get('ND') - processed.get('ND'),
				"late": adjustment.get('LT') - processed.get('LT'),
				"undertime":  adjustment.get('UT') - processed.get('UT'),
				"compensatory":  adjustment.get('CTO') - processed.get('CTO'),
				"processed_work_hrs": processed_time['work'],
				"processed_absent_hrs": processed_time['absent'],
				"processed_undertime_hrs": processed_time['undertime'],
				"processed_nd_hrs": processed_time['nd'],
				"processed_late_hrs": processed_time['late'],
				"processed_overtime_hrs": processed_time['overtime'],
				"processed_cto_hrs": processed_time['cto'],
				"processed_uho_hrs": processed_time['uho'],
				"adjusted_work_hrs": adjustment_time['work'],
				"adjusted_absent_hrs": adjustment_time['absent'],
				"adjusted_undertime_hrs": adjustment_time['undertime'],
				"adjusted_nd_hrs": adjustment_time['nd'],
				"adjusted_late_hrs": adjustment_time['late'],
				"adjusted_overtime_hrs": adjustment_time['overtime'],
				"adjusted_cto_hrs": adjustment_time['cto'],
				"adjusted_uho_hrs": adjustment_time['uho'],
				#Processed Links
				"processed_leave_application_links": str(processed.get('processed_leave_application_links')),
				"processed_overtime_application_links": str(processed.get('processed_overtime_application_links')),
				"processed_official_business_application_links": str(processed.get('processed_official_business_application_links')),
				"processed_excuse_tardiness_application_links": str(processed.get('processed_excuse_tardiness_application_links')),
				"processed_undertime_application_links": str(processed.get('processed_undertime_application_links')),
				"processed_dtr_problem_application_links": str(processed.get('processed_dtr_problem_application_links')),
				"processed_compensatory_time_off_links": str(processed.get('processed_compensatory_time_off_links')),
				"processed_timelogs_application_links": str(processed.get('processed_timelogs_application_links')),
				#Adjusted Links
				"adjusted_leave_application_links": str(adjustment.get('adjusted_leave_application_links')),
				"adjusted_overtime_application_links": str(adjustment.get('adjusted_overtime_application_links')),
				"adjusted_official_business_application_links": str(adjustment.get('adjusted_official_business_application_links')),
				"adjusted_excuse_tardiness_application_links": str(adjustment.get('adjusted_excuse_tardiness_application_links')),
				"adjusted_undertime_application_links": str(adjustment.get('adjusted_undertime_application_links')),
				"adjusted_dtr_problem_application_links": str(adjustment.get('adjusted_dtr_problem_application_links')),
				"adjusted_compensatory_time_off_links": str(adjustment.get('adjusted_compensatory_time_off_links')),
				"adjusted_timelogs_application_links": str(adjustment.get('adjusted_timelogs_application_links')),
			}
			if emp_dict['rate_type'] == "Daily Rate" and adjustment.get('absent_days') != processed.get('absent_days'):
				ab_days = adjustment.get('absent_days') - processed.get('absent_days')
				reg['absent'] = flt(rates.get('daily_rate'), 8) * ab_days			

			if reg.get('absent') or reg.get('unpaid_holiday') or reg.get('overtime') or reg.get('nightdiff') or reg.get('late') or reg.get('undertime') or reg.get('compensatory'):
				adjr = frappe.new_doc("Adjustment Register")
				adjr.update(reg)
				adjr.insert()
				ss_list.append(" " + emp_dict['employee_name'] +"")
		
		self.create_adjustment_processing_logs(reg)

		return self.create_log(ss_list)

	def delete_adjustment(self):
		self.validate_period()
		if not self.exclude_processed_adjustment:
			frappe.db.sql("""DELETE FROM `tabAdjustment Register` WHERE payroll_period = %s  """, (self.period), as_dict=1)
		else:
			frappe.db.sql("""DELETE FROM `tabAdjustment Register` WHERE payroll_period = %s and target_period = %s  """, (self.period, self.target_period), as_dict=1)

	def get_attendance_result(self, emp, attendance, attendance_from, attendance_to, ot_list, ot_map, header, _type):
		ot_class_map = get_ot_class_map()
		rateclass_map = get_rateclass_map()
		prev_adjustment = self.get_previous_adjustment()
		if getdate(emp.get('date_hired')) > getdate(attendance_to):
			frappe.throw(_("You cannot process Employee {0}: {1}, due to Date Hired").format(emp['name'], emp['full_name']))
		attendance_time = {}
		rates = get_rates(emp)
		attendance_result = { "AT": 0.0, "UHO": 0.0, "OT": 0.0, "ND": 0.0, "LT": 0.0, "UT": 0.0, "CTO": 0.0, "absent_days": 0,
			"processed_leave_application_links": [],
			"processed_overtime_application_links": [],
			"processed_official_business_application_links": [],
			"processed_excuse_tardiness_application_links": [],
			"processed_undertime_application_links": [],
			"processed_dtr_problem_application_links": [],
			"processed_compensatory_time_off_links": [],
			"processed_timelogs_application_links": [],
			"adjusted_leave_application_links": [],
			"adjusted_overtime_application_links": [],
			"adjusted_official_business_application_links": [],
			"adjusted_excuse_tardiness_application_links": [],
			"adjusted_undertime_application_links": [],
			"adjusted_dtr_problem_application_links": [],
			"adjusted_compensatory_time_off_links": [],
			"adjusted_timelogs_application_links": [],
		}

		overtimes_register = []
		if emp.get('is_attendance_base') > 0 and getdate(emp.get('date_hired')) < getdate(attendance_to):
			late, overtime, undertime, absent, nightdiff, work_days, absent_days, unpaid_holiday, prev_lwop, prev_absent, is_uho, cto, cto_days = 0, 0, 0, 0, 0, 0, 0, 0, 0 ,0, 0, 0, 0
			before_holiday_work, nwho_days, paid_leave  = 0, 0, 0
			no_previous, dl_days, total_work, pho_days, hourly_basic = 0, 0, 0, 0, 0
			ot_rate_class = frappe.db.get_single_value('Payroll Settings', 'ot_rate_class')
			nd_rate_class = frappe.db.get_single_value('Payroll Settings', 'nd_rate_class')

			#Get OT registers
			unique_ot = ["00000000"]
			ot_register = []
			ot_hrs = "hrs"
			if _type == "adjustment":
				ot_hrs = "ot_hrs"

			for ot in ot_list:
				ot_code = "00000000"
				if ot['ot_code'] in ot_map:
					ot_code = ot['ot_code']
					if ot['ot_code'] not in unique_ot:
						unique_ot.append(ot['ot_code'])

					if emp.get("rate_type") == "Daily Rate":
						amount = flt( ot[ot_hrs], 8) * rates.get('hourly_rate') * (ot_map[ot.get('ot_code')]['daily_rate'] / 100)
						if header.get('ot_rate_class') and emp.get('rate_class'):
							if emp.get('rate_class') in ot_class_map[ot.get('ot_code')]:
								amount = flt( ot[ot_hrs], 8) * rates.get('hourly_rate') * (ot_class_map[ot.get('ot_code')][emp.get('rate_class')][emp.get('rate_type')]['rate'] / 100)
					else:
						amount = flt( ot[ot_hrs], 8) * rates.get('hourly_rate') * (ot_map[ot.get('ot_code')]['rate'] / 100)
						if header.get('ot_rate_class') and emp.get('rate_class'):
							if emp.get('rate_class') in ot_class_map[ot.get('ot_code')]:
								amount = flt( ot[ot_hrs], 8) * rates.get('hourly_rate') * (ot_class_map[ot.get('ot_code')][emp.get('rate_class')]['Monthly Rate']['rate'] / 100)

					if ot.get('ot_code')[-1:] in [1, '1'] and header['nd_rate_class'] and emp.rate_class:
						baseamount, lnd_baseamount, end_baseamount = 0, 0, 0
						if emp.get("rate_type") == "Daily Rate":
							baseamount = rates.get('hourly_rate') * (ot_map[ot.get('ot_code')]['daily_rate'] / 100)
							if header.get('ot_rate_class') and emp.get('rate_class'):
								if emp.get('rate_class') in ot_class_map[ot.get('ot_code')]:									
									#if ot.early_nd:
									#	end_baseamount = flt( ot.early_nd, 8) * rates.get('hourly_rate') * (ot_class_map[ot.get('ot_code')][emp.get('rate_class')][emp.get('rate_type')]['rate'] / 100)
									#if ot.late_nd:
									#	lnd_baseamount = flt( ot.late_nd, 8) * rates.get('hourly_rate') * (ot_class_map[ot.get('ot_code')][emp.get('rate_class')][emp.get('rate_type')]['rate'] / 100)
									baseamount = 0
									if 'early_nd' in rateclass_map[emp.rate_class]:
										end_baseamount = rates.get('hourly_rate') * flt( ot['early_nd'], 8) * (ot_class_map[ot.get('ot_code')][emp.get('rate_class')][emp.get('rate_type')]['rate'] / 100) * (rateclass_map[emp.rate_class]['early_nd'] / 100)
									if 'lt_nd' in rateclass_map[emp.rate_class]:
										lnd_baseamount = rates.get('hourly_rate') * flt( ot['late_nd'], 8) * (ot_class_map[ot.get('ot_code')][emp.get('rate_class')][emp.get('rate_type')]['rate'] / 100) * (rateclass_map[emp.rate_class]['lt_nd'] / 100)
							else:
								baseamount = 0
								if 'early_nd' in rateclass_map[emp.rate_class]:
									end_baseamount = rates.get('hourly_rate') * flt( ot['early_nd'], 8) * (ot_map[ot.get('ot_code')]['daily_rate'] / 100) * (rateclass_map[emp.rate_class]['early_nd'] / 100)
								if 'lt_nd' in rateclass_map[emp.rate_class]:
									lnd_baseamount = rates.get('hourly_rate') * flt( ot['late_nd'], 8) * (ot_map[ot.get('ot_code')]['daily_rate'] / 100) * (rateclass_map[emp.rate_class]['lt_nd'] / 100)
						else:
							baseamount = rates.get('hourly_rate') * (ot_map[ot.get('ot_code')]['rate'] / 100)
							if header.get('ot_rate_class') and emp.get('rate_class'):
								if emp.get('rate_class') in ot_class_map[ot.get('ot_code')]:
									#baseamount = flt( ot[ot_hrs], 8) * rates.get('hourly_rate') * (ot_class_map[ot.get('ot_code')][emp.get('rate_class')]['Monthly Rate']['rate'] / 100)
									#end_baseamount = flt( ot.early_nd, 8) * rates.get('hourly_rate') * (rateclass_map[emp.rate_class]['early_nd'] / 100)
									#lnd_baseamount = flt( ot.late_nd, 8) * rates.get('hourly_rate') * (rateclass_map[emp.rate_class]['lt_nd'] / 100)
									baseamount = 0
									if 'early_nd' in rateclass_map[emp.rate_class]:
										end_baseamount = rates.get('hourly_rate') * flt( ot['early_nd'], 8) * (ot_class_map[ot.get('ot_code')][emp.get('rate_class')]['Monthly Rate']['rate'] / 100) * (rateclass_map[emp.rate_class]['early_nd'] / 100)
									if 'lt_nd' in rateclass_map[emp.rate_class]:
										lnd_baseamount = rates.get('hourly_rate') * flt( ot['late_nd'], 8) * (ot_class_map[ot.get('ot_code')][emp.get('rate_class')]['Monthly Rate']['rate'] / 100) * (rateclass_map[emp.rate_class]['lt_nd'] / 100)
							else:
								baseamount = 0
								if 'early_nd' in rateclass_map[emp.rate_class]:
									end_baseamount = rates.get('hourly_rate') * flt( ot['early_nd'], 8) * (ot_map[ot.get('ot_code')]['rate'] / 100) * (rateclass_map[emp.rate_class]['early_nd'] / 100)
								if 'lt_nd' in rateclass_map[emp.rate_class]:
									lnd_baseamount = rates.get('hourly_rate') * flt( ot['late_nd'], 8) * (ot_map[ot.get('ot_code')]['rate'] / 100) * (rateclass_map[emp.rate_class]['lt_nd'] / 100)
						amount = baseamount + end_baseamount + lnd_baseamount

				ot_register.append({
					"ot_code": ot_code,
					"hrs": flt( ot[ot_hrs], 8),
					"amount": amount, 
					"early_nd": ot.get('early_nd'),
					"late_nd": ot.get('late_nd'),
					"target_date": ot.get('target_date'),
					"employee": ot.get('employee'),
				})

			#Merge all OT Types based on Unique OT and create attendance registers
			for uot in unique_ot:
				merge_amount, merge_hrs, early_nd, late_nd = 0, 0, 0, 0
				target_date = None
				employee = None
				for otr in ot_register:
					if uot == otr.get('ot_code'):
						merge_amount += otr.get('amount')
						merge_hrs += otr.get('hrs')
						if otr.get('early_nd'):
							early_nd += otr.get('early_nd')
						if otr.get('late_nd'):
							late_nd += otr.get('late_nd')
						target_date = otr.get('target_date')
						employee = otr.get('employee')

				if merge_amount > 0:
					overtimes_register.append({
						"pay_code": ot_map[uot]['transaction_type'],
						"pay_time": flt(merge_hrs, 8),
						"amount": flt(merge_amount, 8),
						"early_nd": early_nd,
						"late_nd": late_nd,
						"target_date": target_date,
						"employee": employee,
					})
			
			suc_list = []
			attendance_register = []
			attendance_time = {"work": 0, "absent": 0, "overtime": 0, "nd": 0, "late": 0, "undertime": 0, "cto": 0, "uho": 0}
			if attendance:
				total_cto_days, total_work_days, total_absent_days, total_present_days, total_pho_days, total_hourly_basic, total_nwho_days, total_dl_days = 0, 0, 0, 0, 0, 0, 0, 0
				cur_suc_hol_wout_before, before_holiday_work, before_sp_work = 0, 0, 0
				is_uho, no_previous, dho_amount, work_hrs, paid_leave, total_work = 0, 0, 0, 0, 0, 0
				for at in attendance:
					if _type == 'processed':
						if at["leave_application_links"]:
							attendance_result["processed_leave_application_links"].extend(eval(at["leave_application_links"]))
						if at["overtime_application_links"]:
							attendance_result["processed_overtime_application_links"].extend(eval(at["overtime_application_links"]))
						if at["official_business_application_links"]:
							attendance_result["processed_official_business_application_links"].extend(eval(at["official_business_application_links"]))
						if at["excuse_tardiness_application_links"]:
							attendance_result["processed_excuse_tardiness_application_links"].extend(eval(at["excuse_tardiness_application_links"]))
						if at["undertime_application_links"]:
							attendance_result["processed_undertime_application_links"].extend(eval(at["undertime_application_links"]))
						if at["dtr_problem_application_links"]:
							attendance_result["processed_dtr_problem_application_links"].extend(eval(at["dtr_problem_application_links"]))
						if at["compensatory_time_off_links"]:
							attendance_result["processed_compensatory_time_off_links"].extend(eval(at["compensatory_time_off_links"]))
						if at["timelogs_application_links"]:
							attendance_result["processed_timelogs_application_links"].extend(eval(at["timelogs_application_links"]))
					if _type == 'adjustment':
						if at['lv_links']:
							attendance_result["adjusted_leave_application_links"].extend(at['lv_links'])
						if at['ot_links']:
							attendance_result["adjusted_overtime_application_links"].extend(at['ot_links'])
						if at['ob_links']:
							attendance_result["adjusted_official_business_application_links"].extend(at['ob_links'])
						if at['ext_links']:
							attendance_result["adjusted_excuse_tardiness_application_links"].extend(at['ext_links'])
						if at['ut_links']:
							attendance_result["adjusted_undertime_application_links"].extend(at['ut_links'])
						if at['dtrp_links']:
							attendance_result["adjusted_dtr_problem_application_links"].extend(at['dtrp_links'])
						if at['cto_links']:
							attendance_result["adjusted_compensatory_time_off_links"].extend(at['cto_links'])
						if at['tla_links']:
							attendance_result["adjusted_timelogs_application_links"].extend(at['tla_links'])
						
					cto_days, work_days, absent_days, present_days, pho_days, hourly_basic, nwho_days = 0, 0, 0, 0, 0, 0, 0
					basic_salary, absent, late, undertime, unpaid_holiday, cto, nightdiff = 0, 0, 0, 0, 0, 0, 0
					dl_days, pho_days, uho_days = 0, 0, 0
					if getdate(at['target_date']) == getdate(add_days(attendance_from, -1)):
						no_previous = 1
						if at['is_absent'] or at['is_lwop']:
							is_uho = 1
							if header.get('hd_lwop_as_uho') == 1:
								if (at['lv_status'] == 2 or at['lv_status'] == 3) or at['is_halfday']:
									is_uho = 0
									if at['is_absent']:
										is_uho = 1
						if not at['is_holiday'] and not at['is_restday']:
							cur_suc_hol_wout_before = 0

							if at['work']:
								before_holiday_work = 1
								before_sp_work = 1
							else:
								if at['lv_status'] == 1 and not at['is_lwop']:
									before_holiday_work = 1
									before_sp_work = 1 
								else:
									before_holiday_work = 0
									before_sp_work = 0
					else:
						if getdate(at['target_date']) == getdate(attendance_from):
							if no_previous == 0:
								is_uho = 1

						if not at['is_restday']:
							work_days += 1

						if at['is_holiday'] and at['work'] <= 0:
							nwho_days += 1

						if at['late'] > 0:
							late += flt(at['late'], 8) * flt(rates.get('hourly_rate'), 8)
						
						if at['undertime'] > 0:
							undertime += flt(at['undertime'], 8) * flt(rates.get('hourly_rate'), 8)

						#Get ND
						nd_with_rateclass = 0
						if header['nd_rate_class'] and emp['rate_class']:
							nd_with_rateclass = 1

						if nd_with_rateclass:
							if at['earlynightdiff']:
								nightdiff += at['earlynightdiff'] * (rateclass_map[emp['rate_class']]['early_nd'] / 100) * rates.get('hourly_rate')

							if at['latenightdiff']:
								nightdiff += at['latenightdiff'] * (rateclass_map[emp['rate_class']]['lt_nd'] / 100) * rates.get('hourly_rate')
						else:
							if at['nightdiff']:
								nightdiff += at['nightdiff'] * 0.10 * rates.get('hourly_rate')

						#GET ABSENT
						AT = get_absent_days(at, header)
						if AT > 0:
							absent += ( at['work_hours'] * flt(AT, 8) ) * flt(rates.get('hourly_rate'), 8) #get total absent amount
							absent_days += AT #add to employee total absent days
							#AT_days += AT #add to current day total absent days
							#test.append(_(""+cstr(at.target_date)+" "+cstr(absent_days)+" "+cstr(at.work_hours * flt(AT, 8))+" "+cstr(flt(rates.get('hourly_rate'), 8))+"")) #test script for absent
							
						if at['cto']:
							max_cto = 0
							max_cto += at['undertime']
							max_cto += at['late']
							if ( at['is_absent'] == 1 or at['is_lwop'] == 1 ) and not at['is_holiday']:
								if at['is_lwop'] == 1 and at['lv_status'] > 1:
									max_cto += ( at['work_hours'] / 2 )
								else:
									max_cto += ( at['work_hours'] / 2 ) if at['is_halfday'] == 1 else at['work_hours']

							if max_cto < at['cto']:
								cto += ( max_cto ) * flt(rates.get('hourly_rate'), 8)
							else:
								cto += ( at['cto'] ) * flt(rates.get('hourly_rate'), 8)

							if at['is_absent'] == 1:
								if at['is_halfday'] == 1 and max_cto >= (at['work_hours'] / 2):
									cto_days += 0.5
								elif max_cto >= at['work_hours']:
									cto_days += 1

						dh_exemption = 0
						ho_paid = 0 # set default not paid on holiday
						if emp.get("rate_type") == "Daily Rate":
							dl_absent = 1 #set default alaways absent

							#check if employee is not absent
							if(at['work'] or (not at['is_absent'])) and (not at['is_lwop']):
								dl_absent = 0

							#if did not worked on a holiday tagged as uho
							if at['is_holiday'] and at['work'] < 1 and not (at['is_restday']):
								dl_absent = 1

							#leave triggers
							if at['lv_status'] and (not at['is_lwop']):
								if at['lv_status'] == 1:
									dl_absent = 0
								elif at['lv_status'] > 1:
									dl_absent = 0
							
							#check if holiday
							if at['is_holiday']:
								if at['is_restday']:
									if (not at['is_sp_holiday']) and (not is_uho) and (not header.get('disable_pdhord')):
										ho_paid = 1 #paid on regular holiday if not UHO
								else:
									if dl_absent == 1 and at['is_sp_holiday'] and header.get('uho_ab_spnw'):
										ho_paid = 0 #not paid holiday on special HO
									elif dl_absent == 1 and (not is_uho) and (not at['is_sp_holiday']):
										if not header.get('ab_regho'): #if not absent on regular HO
											ho_paid = 1 #paid holiday if absent and not UHO
									elif dl_absent == 0:
											ho_paid = 1  
								if (not at['is_sp_holiday']) and ho_paid == 0 and header.get('ignore_uho'):
									ho_paid = 1 
									dh_exemption = 1
									
							else: 
								if dl_absent == 0 and (not at['is_restday']):
									if at['is_halfday']:
										dl_days += 0.5
									else:
										dl_days += 1

							#check if lwop halfday
							if dl_absent == 1 and at['is_lwop']:
								# if lwop halfday plus half day
								if at['lv_status'] > 1:
									if at['is_halfday']: #if lwop halfday with absent halfday absent is wholeday absent
										if at['work']:
											dl_days += 0.5
										else:
											dl_days += 0
									else:
										dl_days += 0.5

						#double holiday
						if at['is_db_holiday']:
							if not header.get('dis_dho_tran'):
								if not header.get('dho'):
									frappe.throw(_("Must have Double Holiday Transaction Type in Payroll Settings"))

								if emp.get("rate_type") == "Daily Rate":
									if ho_paid == 1 and dh_exemption == 0:
										dho_amount += flt(rates.get('daily_rate'), 8)*1
										register.append({"pay_code": header.get('dho'), "amount": dho_amount})

								if emp.get("rate_type") != "Daily Rate":
									if not is_uho or at['work']:
										dho_amount += flt(rates.get('daily_rate'), 8)*1
										register.append({"pay_code": header.get('dho'), "amount": dho_amount})
									
						if ho_paid == 1:
							pho_days += ho_paid
						
						#set Special holiday to UHO if not work On the Day Before Holiday
						if at['is_holiday'] and at['is_sp_holiday']:
							if emp.get("rate_type") == "Daily Rate":
								if cur_suc_hol_wout_before <= 1:
									is_uho = 1
							if emp.get("rate_type") != "Daily Rate":
								if before_sp_work:
									is_uho = 0
								else:
									is_uho = 1

						#suc_list.append({"Date": at.target_date, "UHO": is_uho})
						if at['is_holiday'] == 1 and is_uho == 1 and (not at['is_ob']) and not at['is_restday']:
							#if present not UHO
							if emp.get("rate_type") != "Daily Rate":
								if at['work'] and (not at['is_lwop']) and (not at['is_absent']) and (not at['is_restday']) and (not at['is_halfday']):
									is_uho = 0
								elif header.get('ex_uho_spnw') and at['is_sp_holiday']:
									is_uho = 0								
								else:
									if at['is_absent'] and header.get('mo_abho'):
										pass
									else:
										if not at['work']:
											unpaid_holiday += at['work_hours'] * flt(rates.get('hourly_rate'), 8)
										if header.get('uho_ab_days') == 1:
											absent_days += 1
											#AT_days += 1
						suc_list.append({"Date": at['target_date'], "NO": is_uho})
						#check if this attendance is lwop or absent for next attendance
						if is_uho == 1:
							#if present
							if at['work'] and (not at['is_lwop']) and (not at['is_absent']) and (not at['is_restday']) and (not at['is_halfday']):
								is_uho = 0

							#if Halfday next day
							if header.get('hd_no_uho') and at['is_halfday']:
								is_uho = 0

							#if Proper Leave next day is not UHO
							if at['lv_status'] == 1 and not at['is_lwop']:
								is_uho = 0

							#if proper OB next day is not UHO
							if at['is_ob']:
								is_uho = 0	

							#UHO if Absent and leave withoutpay
							if at['is_absent'] and at['is_lwop']:
								is_uho = 1

							#Not UHO if halfday and halfday leave
							if at['lv_status'] > 1 and at['is_halfday']:
								is_uho = 0

							#if setting Half Day LWOP plus Half Day Work is Considered as Paid Holiday
							if at['lv_status'] > 1 and at['work'] and header.get('hd_lwop_as_uho') == 1 and at['is_lwop'] and (not at['is_absent']):
								is_uho = 0
						
							#strictly No UHO if CTO can cover absent work hours
							if at['is_absent'] and at['work_hours'] <= at['cto']:
								is_uho = 0

						else:
							is_uho = 0
							if (at['is_absent'] or at['is_lwop']) and not at['is_ob']:
								is_uho = 1

								if header.get('hd_lwop_as_uho') == 1:
									if (at['lv_status'] == 2 or at['lv_status'] == 3) and at['is_halfday']:
										is_uho = 0
										if at['is_absent']:
											is_uho = 1

							#If Halfday is LWOP but not absent with setting
							if header.get('hd_lwop_as_uho') == 1 and at['is_lwop']:
								if (at['lv_status'] == 2 or at['lv_status'] == 3) and (not at['is_absent']):
									is_uho = 0
							
							#strictly No UHO if CTO can cover absent work hours
							if at['is_absent'] and at['work_hours'] <= at['cto']:
								is_uho = 0

							#if Halfday next day will not be UHO
							if header.get('hd_no_uho') and at['is_halfday']:
								is_uho = 0

						if emp.get("rate_type") == "Hourly Rate":
							hour_bs = ((work_days - absent_days) * at['work_hours']) * flt(rates.get('hourly_rate'), 8)
							hourly_basic += hour_bs

						#Check if employee has attendance
						if at['work'] or at['overtime']:
							total_work += at['work']
							total_work += at['overtime']

						if not at['is_restday'] and not at['is_holiday']:
							if AT < 1:
								paid_leave = 1

						#Succesive Holiday Without attendance Before the start 
						if not at['is_holiday'] and not at['is_restday']:
							cur_suc_hol_wout_before = 0
							if at['work']:
								before_holiday_work = 1
								before_sp_work = 1
							else:
								if at['lv_status'] == 1 and not at['is_lwop']:
									before_holiday_work = 1
									before_sp_work = 1
								else:
									before_holiday_work = 0
									before_sp_work = 0
 
						if at['is_holiday'] and not at['is_sp_holiday']:
							if before_holiday_work:
								if cur_suc_hol_wout_before:
									cur_suc_hol_wout_before += 1
								else:
									cur_suc_hol_wout_before = 1
							else:
								if at['work']:
									before_holiday_work = 1
								else:
									if at['lv_status'] == 1 and not at['is_lwop']:
										before_holiday_work = 1

						if at['is_holiday'] and at['is_sp_holiday']:
							cur_suc_hol_wout_before = 0

							if at['work']:
								before_holiday_work = 1
							else:
								before_holiday_work = 0

						#Get Presentdays and Daily Rate should have no absent
						if emp.get("rate_type") == "Daily Rate":
							absent = 0
							present_days = dl_days
						else:
							present_days =  work_days - absent_days

						if emp.get("rate_type") == "Daily Rate":
							absent = 0

						if header.get('ignore_uho'):
							unpaid_holiday = 0

						if emp.get('ignore_late'):
							late = 0

						if emp.get('ignore_ut'):
							undertime = 0

						if emp.get('ignore_nd') or header.get('ignore_nd'):
							nightdiff = 0

						cost_center = emp.get("cost_center")
						if 'cost_center' in at and at['cost_center']:
							cost_center = at['cost_center']
						 
						if emp.get("rate_type") == "Daily Rate":
							basic_salary = (((dl_days + pho_days) - uho_days) * at['work_hours']) * flt(rates.get('hourly_rate'), 8)
							work_hrs += ((dl_days) * at['work_hours'])

						total_cto_days += cto_days
						total_work_days += work_days
						total_absent_days += absent_days
						total_present_days += present_days
						total_pho_days += pho_days
						total_hourly_basic += hourly_basic
						total_nwho_days += nwho_days
						total_dl_days += dl_days

						attendance_register.append({
							"BS": basic_salary,
							"AT": absent,
							"LT": late,
							"UT": undertime,
							"UHO": unpaid_holiday,
							"CTO": cto,
							"ND": nightdiff,
							"cost_center": cost_center,
						})

						attendance_time['work'] += at['work']
						attendance_time['absent'] += absent_days * at['work_hours']
						attendance_time['overtime'] += at['overtime']
						attendance_time['nd'] += at['nightdiff']
						attendance_time['late'] += at['late']
						attendance_time['undertime'] += at['undertime']
						attendance_time['cto'] += at['cto']
						attendance_time['uho'] += unpaid_holiday / flt(rates.get('hourly_rate'), 8)

					#Create Adjustment Register Processed
					if self.exclude_processed_adjustment:
						create_pass = 0
						for p in prev_adjustment:
								
							if (at["employee"] == p["employee"] and at["work"] == p["worked_hours"] and getdate(at["target_date"]) == getdate(p["date"]) and at["late"] == p["late_hours"]
							and at["overtime"] == p["overtime_hours"] and at["overtime_nd"] == p["overtime_nd_hours"] and at["overtime_ex"] == p["overtime_ex_hours"] and at["undertime"] == p["undertime_hrs"]
							and at["cto"] == p["cto"] and at["nightdiff"] == p["night_difference_hours"]):
								create_pass = 1
									
						if create_pass == 0:
							self.create_adjustment_register_processed(at, _type)

					else:
						frappe.throw(_("create_pass"))
						self.create_adjustment_register_processed(at, _type)

						# Save work For Next Day in Attendace Processing
				header['no_attendance'] = 1
				#frappe.throw(_(suc_list))
				if total_work > 0 or paid_leave > 0 or total_cto_days > 0:
					header['no_attendance'] = 0
				if emp.get("rate_type") == "Daily Rate":
					if total_dl_days > 0:
						header['no_attendance'] = 0

				#attendance_register.append({"pay_code": "AT", "amount": flt(absent, 8) })
				#attendance_register.append({"pay_code": "CTO", "amount": flt(cto, 8) })
				#attendance_register.append({"pay_code": "UHO", "amount": flt(unpaid_holiday, 8) })
				#attendance_register.append({"pay_code": "OT", "amount": flt(overtime, 8) })
				#attendance_register.append({"pay_code": "ND", "amount": flt(nightdiff, 8) })
				#attendance_register.append({"pay_code": "LT", "amount": flt(late, 8) })
				#attendance_register.append({"pay_code": "UT", "amount": flt(undertime, 8) })
				
				#for d in attendance_register:
				#	register.append(d)
				if self.exclude_processed_adjustment:
					past_overtime = frappe.db.sql("""SELECT * FROM `tabOvertime Adjustment Register` WHERE previous_payroll_period = %s AND current_payroll_period != %s 
						""",(self.period, self.target_period), as_dict=1)
				for otr in overtimes_register:
					overtime += otr.get('amount')
					if _type == "adjustment":
						if self.exclude_processed_adjustment:
							created_overtime_reg = 0
							if past_overtime:
								count = 0
								for p in past_overtime:
									count += 1
									#if count == 2:
									#	frappe.throw(_(otr['employee']))
									#if count == 2:
									#	frappe.throw(_(otr['target_date']))
									if getdate(p['target_date']) == getdate(otr['target_date']) and p['ot_code'] == otr['pay_code'] and p['hrs'] == otr['pay_time'] and p['early_nd'] == otr['early_nd'] and p['late_nd'] == otr['late_nd'] and p['employee'] == otr['employee']:
										created_overtime_reg = 1
								if created_overtime_reg == 0:
									self.create_overtime_adjustment_register(otr)
						else:
							self.create_overtime_adjustment_register(otr)

				attendance_payment = self.create_attendance_registers(header, attendance_register)
				if attendance_payment:
					for atp in attendance_payment:
						attendance_result[atp["pay_code"]] = flt(atp["amount"], 8)
	
				attendance_result.update({ 
					#"AT": flt(absent, 8), 
					#"UHO": flt(unpaid_holiday, 8), 
					"OT": flt(overtime, 8), 
					#"ND": flt(nightdiff, 8), 
					#"LT": flt(late, 8), 
					#"UT":flt(undertime, 8), 
					#"CTO":flt(cto, 8), 
					"absent_days": total_absent_days, 
					"wk_days": total_work_days 
				})
				header["absent_days"] = total_absent_days
				attendance_result["absent_days"] = total_absent_days
				#attendance_result.update({ "ab": flt(absent, 8), "uho": flt(unpaid_holiday, 8), "ot": flt(overtime, 8), "nd": flt(nightdiff, 8), "lt": flt(late, 8), "ut":flt(undertime, 8), "cto":flt(cto, 8), "ab_days": absent_days, "wk_days": work_days })
			else:
				header['no_attendance'] = 1
		
		return attendance_result, attendance_time
	def get_previous_adjustment(self):
		prev_adjustment = frappe.db.sql("""SELECT * FROM `tabAdjustment Register Adjusted` WHERE payroll_period = %s AND target_period != %s 
						""",(self.period, self.target_period), as_dict=1)
		return prev_adjustment

	def create_overtime_adjustment_register(self, otr):
		new_doc = frappe.new_doc("Overtime Adjustment Register")
		new_doc.employee = otr.get("employee")
		new_doc.employee_name = frappe.db.get_value('Employee', otr.get("employee"), 'full_name')
		new_doc.company = self.company
		new_doc.previous_payroll_period = self.period
		new_doc.current_payroll_period = self.target_period
		new_doc.target_date = otr.get("target_date")
		new_doc.ot_code = otr.get("pay_code")
		new_doc.hrs = otr.get("pay_time")
		new_doc.linked_ot = None
		new_doc.early_nd = otr.get("early_nd")
		new_doc.late_nd = otr.get("late_nd")
		new_doc.flags.ignore_permissions = True
		new_doc.insert()

	def create_adjustment_register_processed(self, at, _type):
		new_doc = None
		if _type == "adjustment":
			new_doc = frappe.new_doc("Adjustment Register Adjusted")
			new_doc.worked_hours = at["work"]
			new_doc.overtime_nd_ex_hours = at["overtime_ndex"]
		if _type == "processed":
			new_doc = frappe.new_doc("Adjustment Register Processed")
			new_doc.worked_hours = at["work"]
			new_doc.overtime_nd_ex_hours = at["ot_ndex"]
			
		if new_doc:
			new_doc.employee = at["employee"]
			new_doc.employee_name = frappe.db.get_value('Employee', at["employee"], 'full_name')
			new_doc.company = self.company
			new_doc.payroll_period = self.period
			new_doc.target_period = self.target_period
			new_doc.date = at["target_date"]
			new_doc.late_hours = at["late"]
			new_doc.overtime_hours = at["overtime"]
			new_doc.overtime_nd_hours = at["overtime_nd"]
			new_doc.overtime_ex_hours = at["overtime_ex"]
			new_doc.night_difference_hours = at["nightdiff"]
			new_doc.undertime_hrs = at["undertime"]
			new_doc.cto = at["cto"]
			new_doc.tags = at["tags"]
			new_doc.links = at["links"]
			new_doc.flags.ignore_permissions = True
			new_doc.insert()

	def create_attendance_registers(self, header, attendance):
		register = []
		cc_list = []
		basic = 0
		paying_cc = []

		#get unique cost centers
		for atc in attendance:
			if atc['cost_center'] not in cc_list:
				cc_list.append(atc['cost_center'])

		for cc in cc_list:
			BS, AT, LT, UT, UHO, ND, CTO = 0, 0, 0, 0, 0, 0, 0
			for d in attendance:
				if d['cost_center'] == cc:
					basic += d['BS']
					BS += d['BS']
					AT += d['AT']
					LT += d['LT']
					UT += d['UT']
					UHO += d['UHO']
					ND += d['ND']
					CTO += d['CTO']

					if d['BS'] > 0:
						paying_cc.append(cc)

			#Create Registers per Cost Centers
			register.append({"pay_code": "BS", "amount": flt(BS, 8), "cost_center": cc })
			register.append({"pay_code": "AT", "amount": flt(AT, 8), "cost_center": cc })
			register.append({"pay_code": "LT", "amount": flt(LT, 8), "cost_center": cc })
			register.append({"pay_code": "UT", "amount": flt(UT, 8), "cost_center": cc })
			register.append({"pay_code": "UHO", "amount": flt(UHO, 8), "cost_center": cc })
			register.append({"pay_code": "ND", "amount": flt(ND, 8), "cost_center": cc })
			register.append({"pay_code": "CTO", "amount": flt(CTO, 8), "cost_center": cc })
		
		#set daily rate employee basic rate
		header['daily_basic'] = basic 
		#remove duplicate paying cc
		#header['paying_cc'] = list(dict.fromkeys(paying_cc))
		return register	

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

	def create_adjustment_processing_logs(self, header):
		pr = frappe.new_doc("Adjustment Processing Logs")
		pr.update(header)
		pr.update({
			'company': self.company,
			'period': self.period,
			'target_period': self.target_period,
			'employee': self.employee,
			'department': self.department,
			'location': self.location,
			'payroll_date': self.payroll_date,
			'frequency': self.frequency,
			'schedule': self.schedule,
			'period_from': self.period_from,
			'attendance_from': self.attendance_from,
			'period_group': self.period_group,
			'period_to': self.period_to,
			'attendance_to': self.attendance_to,
			'user': frappe.session.user,
			'user_name': frappe.db.get_value("User",{"name":frappe.session.user}, "full_name"),
			'user_ip': frappe.local.request_ip,
		})
		pr.flags.ignore_permissions = True
		pr.insert()

	def validate_adjustment_period(self, employees):
		proc_ar_emp = []
		ar_list = frappe.get_all('Adjustment Register', filters={'payroll_period': self.period}, fields=['*'])
		for ar in ar_list:
			if ar.target_period != self.target_period:
				proc_ar_emp.append(ar.employee)

				if self.employee and ar.employee == self.employee:
					if not self.exclude_processed_adjustment:
						frappe.throw(_( "Adjustment already processed in {0}".format(ar.target_period) ))

		for emp in employees:
			if emp.name in proc_ar_emp:
				del emp

		return employees