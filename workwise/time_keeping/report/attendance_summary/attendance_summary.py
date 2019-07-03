# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr, add_to_date, get_datetime
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_schedule, get_holiday_list, get_leave_list, get_shift_map, get_card_within, 
get_attendance, get_defaults, get_ob_list, get_ot_list, 
get_ut_list, get_ext_list, get_cto_list, get_sorted_card, get_wss_list, insert_overtime,init_employee_map,complete_sched,get_template_map)

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
			"label": _("Time IN"),
			"fieldtype": "Data",
			"width": 140
		},
	]

	if filters.show_break:
		columns += [
			{
				"fieldname": "break_out",
				"label": _("Break OUT"),
				"fieldtype": "Data",
				"width": 140
			},
			{
				"fieldname": "break_in",
				"label": _("Break IN"),
				"fieldtype": "Data",
				"width": 140
			}
		]

	columns += [
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

	return columns

def get_result(filters):
	validate_filters(filters)
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def validate_filters(filters):
	if not filters.payroll_period:
		frappe.throw("Filter Payroll Period is Required")

	if not filters.employee:
		frappe.throw("Filter Employee is Required")

	if not filters.time_options:
		frappe.throw("Filter Time Options is Required")

def get_employees(filters):
	employees = frappe.db.sql("""SELECT `name`, full_name, biometrics_id, company, rate_type,
		location, department, is_attendance_base, no_hours FROM tabEmployee WHERE `name` = %(employee)s
		AND is_active = 1 LIMIT 1 """,{ 
			"employee": filters.employee
		}, as_dict=True)

	return employees

def get_data(filters):
	#Initialize
	data = []
	employees = get_employees(filters)
	
	shift_map = get_shift_map()
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

	if employees:
		pay_from, pay_to, approval_cutoff = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to", "approval_cutoff"])
		employee_list = convert_to_list(employees)
		template_map = get_template_map()
		shift_map = get_shift_map()
		emp_map = init_employee_map(employees, filters.company, pay_from, pay_to, approval_cutoff, filters.show_adjusted)
		for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
			complete_sched(emp_dict, pay_from, pay_to, template_map)
			for sched in emp_dict['schedules']:
				entry = get_defaults(emp_dict.get('employee_details'), sched, shift_map)
				cards_in, cards_out = get_card_within(entry.get('pre_shift'), entry.get('end_preshift'), 
					entry.get('post_shift'), entry.get('end_postshift'), emp_dict.get('timecards'))
				get_sorted_card(entry, cards_in, cards_out)
				get_attendance(entry, emp_dict.get('lvs'), emp_dict.get('hls'), emp_dict.get('obs'), 
					emp_dict.get('ots'), emp_dict.get('uts'), emp_dict.get('ext'), emp_dict.get('cto'), emp_dict.get('wss'))

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