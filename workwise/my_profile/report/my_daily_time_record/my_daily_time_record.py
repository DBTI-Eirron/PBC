# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, calendar, time
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from time import strptime
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_schedule, get_holiday_list, get_leave_list, 
get_shift_map, get_card_within, get_attendance, get_defaults, get_ob_list, get_ot_list, 
get_ut_list, get_ext_list, get_cto_list, get_sorted_card, get_wss_list )

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
	]

	return columns

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_employees(filters):
	employees = frappe.db.sql("""SELECT * FROM `tabEmployee` WHERE user_id  = %(user)s """,{ "user": frappe.session.user }, as_dict=True)

	return employees

def get_data(filters):
	#Initialize
	data = []
	pay_from, pay_to, approval_cutoff = "", "", ""
	employees = get_employees(filters)
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
	
	if filters.month and filters.year and not filters.payroll_period:
		pay_from = str(int(filters.month) + 1)+"-01-"+filters.year
		pay_to = str(int(filters.month) + 1)+"-"+str(calendar.monthrange(int(filters.year), int(filters.month) + 1)[1])+"-"+filters.year
		pay_from = getdate(str(pay_from))
		pay_to = getdate(str(pay_to))
	if filters.payroll_period:
		pay_from, pay_to, approval_cutoff = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to", "approval_cutoff"])

	shift_map = get_shift_map()
	for emp in employees:
		timecard_list = get_timecard_list(emp.biometrics_id, pay_from, pay_to + datetime.timedelta(days=1))
		holidays = get_holiday_list(emp.company, emp.location, pay_from, pay_to)
		schedule = get_schedule(emp.name, pay_from, pay_to)
		leaves = get_leave_list(emp.name, pay_from, pay_to, approval_cutoff, filters.show_adjusted)
		ots = get_ot_list(emp.name, pay_from, pay_to, approval_cutoff, filters.show_adjusted)
		obs = get_ob_list(emp.name, pay_from, pay_to, approval_cutoff, filters.show_adjusted)
		uts = get_ut_list(emp.name, pay_from, pay_to, approval_cutoff, filters.show_adjusted)
		ext = get_ext_list(emp.name, pay_from, pay_to, approval_cutoff, filters.show_adjusted)
		cto = get_cto_list(emp.name, pay_from, pay_to, approval_cutoff, filters.show_adjusted)
		wss = get_wss_list(emp.name, pay_from, pay_to, approval_cutoff, filters.show_adjusted)

		for sched in schedule:
			entry = get_defaults(emp, sched, shift_map)
			cards_in, cards_out = get_card_within(entry.get('pre_shift'), entry.get('end_preshift'), entry.get('post_shift'), entry.get('end_postshift'), timecard_list)
			get_sorted_card(entry, cards_in, cards_out)
			get_attendance(entry, leaves, holidays, obs, ots, uts, ext, cto, wss)

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