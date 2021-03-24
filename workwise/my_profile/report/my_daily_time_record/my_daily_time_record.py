# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, calendar, time
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from time import strptime
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_schedule, get_holiday_list, get_leave_list, get_shift_map, get_card_within, 
get_attendance, get_defaults, get_ob_list, get_ot_list, get_multi_breaks,
get_ut_list, get_ext_list, get_cto_list, get_sorted_card, get_wss_list, insert_overtime,init_employee_map,complete_sched,change_sched,get_template_map, processed_def_sched)

def execute(filters=None):
	columns = get_columns(filters)
	results = get_result(filters)
	return columns, results

def get_columns(filters):
	columns = [
		{
			"fieldname": "target_date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 80
		},
		{
			"fieldname": "work_shift",
			"label": _("Shift"),
			"fieldtype": "Link",
			"options": "Work Shift",
			"width": 130
		},
		{
			"fieldname": "card_in",
			"label": _("Time In"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "break_out",
			"label": _("Break Out"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "break_in",
			"label": _("Break In"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "card_out",
			"label": _("Time Out"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "work",
			"label": _("Work"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "break",
			"label": _("Break"),
			"fieldtype": "Float",
			"width": 60
		},		
		{
			"fieldname": "late",
			"label": _("Late"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "overtime",
			"label": _("OT"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "overtime_nd",
			"label": _("OT ND"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "overtime_ex",
			"label": _("OT EX"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "nightdiff",
			"label": _("ND"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "undertime",
			"label": _("UT"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "cto",
			"label": _("CTO"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "tags",
			"label": _("Tags"),
			"fieldtype": "Data",
			"width": 400
		},
		{
			"fieldname": "links",
			"label": _("Links"),
			"fieldtype": "Data",
			"width": 400
		},
	]
	
	if filters.flt_precision:
		precision_fields = ["work","break","late","overtime","overtime_ex","overtime_nd","nightdiff","cto","undertime"]
		for d in columns:
			if d.get('fieldname') in precision_fields:
				d['precision'] = cint(filters.flt_precision)

	return columns

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_employees(filters):
	employee = ""
	employees = frappe.db.sql("""SELECT * FROM `tabEmployee` WHERE user_id  = %(user)s """,{ "user": frappe.session.user }, as_dict=True)
	for d in employees:
		employee = d.name

	return employees, employee

def get_data(filters):
	#Initialize
	data = []
	pay_from, pay_to, approval_cutoff = "", "", ""
	employees, employee = get_employees(filters)
	totals = {
		'card_out': '<b> Totals </b>',
		'break': 0,
		'work': 0,
		'late': 0,
		'undertime': 0,
		'overtime': 0,
		'overtime_nd': 0, 
		'overtime_ex': 0, 
		'nightdiff': 0,
		'cto': 0,
	}
	
	shift_map = get_shift_map()
	if employees:
		data = []
		adjustment = 0
		monthly_approval_cutoffs = 0
		if filters.month and filters.year and not filters.payroll_period:
			pay_from = str(int(filters.month) + 1)+"-01-"+filters.year
			pay_to = str(int(filters.month) + 1)+"-"+str(calendar.monthrange(int(filters.year), int(filters.month) + 1)[1])+"-"+filters.year
			pay_from = getdate(str(pay_from))
			pay_to = getdate(str(pay_to))

		if filters.payroll_period:
			pay_from, pay_to, approval_cutoff = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to", "approval_cutoff"])

		employee_list = convert_to_list(employees)
		template_map = get_template_map()
		shift_map = get_shift_map()

		if filters.show_adjusted:
			adjustment = 1
		if filters.month and filters.year and not filters.payroll_period:
			monthly_approval_cutoffs = 1

		emp_map = init_employee_map(employees, filters.employee, filters.company, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs)

		for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
			complete_sched(emp_dict, pay_from, pay_to, template_map)
			change_sched(emp_dict, emp_dict['schedules'], emp_dict.get('csa'))
			if filters.show_adjusted:
				processed_def_sched(emp, pay_from, pay_to, emp_dict['schedules'])
			for sched in emp_dict['schedules']:
				entry = get_defaults(emp_dict.get('employee_details'), sched, shift_map, emp_dict.get('overrides'))
				cards_in, cards_out = get_card_within(entry, sched['target_date'], emp_dict['timelogs_map'], emp_dict['schedules'], shift_map, entry.get('pre_shift'), entry.get('end_preshift'), 
					entry.get('post_shift'), entry.get('end_postshift'), emp_dict.get('timecards'), emp_dict.get('dtrp'), emp_dict.get('tla'))
				get_sorted_card(entry, cards_in, cards_out, emp_dict['timelogs_map'])
				get_multi_breaks(entry, cards_in, cards_out)
				get_attendance(entry, emp_dict.get('overrides'),emp_dict.get('lvs'), emp_dict.get('hls'), emp_dict.get('obs'), emp_dict.get('ots'), 
					emp_dict.get('uts'), emp_dict.get('ext'), emp_dict.get('cto'), emp_dict.get('wss'), emp_dict.get('dtrp'), emp_dict.get('tla'))

				entry['break'] = convert_secs(filters, entry['break'])
				totals['break'] += entry['break']
				entry['work'] = convert_secs(filters, entry['work'])
				totals['work'] += entry['work']
				entry['late'] = convert_secs(filters, entry['late'])
				totals['late'] += entry['late']
				entry['overtime'] = convert_secs(filters, entry['overtime'])
				totals['overtime'] += entry['overtime']
				entry['overtime_nd'] = convert_secs(filters, entry['overtime_nd'])
				totals['overtime_nd'] += entry['overtime_nd']
				entry['overtime_ex'] = convert_secs(filters, entry['overtime_ex'])
				totals['overtime_ex'] += entry['overtime_ex']
				entry['nightdiff'] = convert_secs(filters, entry['nightdiff'])
				totals['nightdiff'] += entry['nightdiff']
				entry['undertime'] = convert_secs(filters, entry['undertime'])
				totals['undertime'] += entry['undertime']			
				entry['cto'] = convert_secs(filters, entry['cto'])
				totals['cto'] += entry['cto']
				data.append(entry)
		data.append(totals)
		
	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)
	return result

def convert_secs(filters, secs):
	con = 0
	if filters.time_options == "Mins":
		con = flt(secs, 8) / 60
	else:
		con = flt(secs, 8) / 3600
	return flt(con, 8)

def convert_to_list(dic):
	data = []
	for d in dic:
		data.append(d.name)
	return data