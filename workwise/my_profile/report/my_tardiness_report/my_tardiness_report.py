# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr, add_to_date, get_datetime
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_schedule, get_holiday_list, get_leave_list, get_shift_map, get_card_within, 
get_attendance, get_defaults, get_ob_list, get_ot_list, 
get_ut_list, get_ext_list, get_cto_list, get_sorted_card, get_wss_list, insert_overtime,init_employee_map,complete_sched,change_sched,get_template_map)

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_data(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "target_date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "work_shift",
			"label": _("Shift"),
			"fieldtype": "Link",
			"options": "Work Shift",
			"width": 180
		},
		{
			"fieldname": "card_in",
			"label": _("Time IN"),
			"fieldtype": "Date",
			"width": 140
		},
		{
			"fieldname": "card_out",
			"label": _("Time OUT"),
			"fieldtype": "Date",
			"width": 140
		},
		{
			"fieldname": "work",
			"label": _("Work"),
			"fieldtype": "Float",
			"width": 80
		},
		{
			"fieldname": "late",
			"label": _("Late"),
			"fieldtype": "Float",
			"width": 80
		},
		{
			"fieldname": "undertime",
			"label": _("Undertime"),
			"fieldtype": "Float",
			"width": 80
		},
	]

	return columns

def get_employees(filters):
	employees = []
	emp = frappe.db.sql(""" SELECT name, `user_id` FROM `tabEmployee` WHERE user_id = %s AND user_id != "" AND user_id is not null LIMIT 1""",( frappe.session.user ), as_dict=1)
	if emp:
		employees = frappe.db.sql("""SELECT `name`, full_name, biometrics_id, company, rate_type,
			location, department, is_attendance_base, no_hours, default_schedule FROM tabEmployee WHERE `name` = %(employee)s
			AND is_active = 1 LIMIT 1 """,{ 
				"employee": emp[0].name
			}, as_dict=True)

	if not employees:
		frappe.throw(_("No Record Found"))

	return employees

def get_data(filters):
	#Initialize
	data = []
	employees = get_employees(filters)
	totals = {
		"target_date": None,
		"work_shift": None,
		"card_in": None,
		"card_out": None,
		"work": 0,
		"late": 0,
		"undertime": 0,
	}

	if employees:
		pay_from = filters.from_date
		pay_to = filters.to_date
		employee_list = convert_to_list(employees)
		template_map = get_template_map()
		shift_map = get_shift_map()
		emp_map = init_employee_map(employees, employees[0]['name'], employees[0]['company'], pay_from, pay_to, None, 0)
		for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
			complete_sched(emp_dict, pay_from, pay_to, template_map)
			change_sched(emp_dict, emp_dict['schedules'], emp_dict.get('csa'))
			for sched in emp_dict['schedules']:
				entry = get_defaults(emp_dict.get('employee_details'), sched, shift_map, emp_dict.get('overrides'))
				cards_in, cards_out = get_card_within(sched['target_date'], emp_dict['timelogs_map'], emp_dict['schedules'], shift_map, entry.get('pre_shift'), entry.get('end_preshift'), 
					entry.get('post_shift'), entry.get('end_postshift'), emp_dict.get('timecards'), emp_dict.get('dtrp'), emp_dict.get('tla'))
				get_sorted_card(entry, cards_in, cards_out, emp_dict['timelogs_map'])
				get_attendance(entry, emp_dict.get('overrides'),emp_dict.get('lvs'), emp_dict.get('hls'), emp_dict.get('obs'), 
					emp_dict.get('ots'), emp_dict.get('uts'), emp_dict.get('ext'), emp_dict.get('cto'), emp_dict.get('wss'), emp_dict.get('dtrp'), emp_dict.get('tla'))

				entry['break'] = convert_secs(filters, entry['break'])
				entry['work'] = convert_secs(filters, entry['work'])
				entry['late'] = convert_secs(filters, entry['late'])
				entry['overtime'] = convert_secs(filters, entry['overtime'])
				entry['overtime_nd'] = convert_secs(filters, entry['overtime_nd'])
				entry['overtime_ex'] = convert_secs(filters, entry['overtime_ex'])
				entry['nightdiff'] = convert_secs(filters, entry['nightdiff'])
				entry['undertime'] = convert_secs(filters, entry['undertime'])
				entry['cto'] = convert_secs(filters, entry['cto'])
				totals['work'] += entry['work']
				totals['late'] += entry['late']
				totals['undertime'] += entry['undertime']
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