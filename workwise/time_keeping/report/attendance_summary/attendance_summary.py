# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_schedule, get_holiday_list, get_leave_list, 
get_shift_map, get_card_within, get_attendance, get_defaults, get_ob_list, get_ot_list, get_ut_list, get_ext_list)

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
			"fieldname": "undertime",
			"label": _("UT"),
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
	employees = frappe.db.sql("""SELECT `name`, full_name, biometrics_id, company, location, is_attendance_base, no_hours FROM tabEmployee WHERE `name` = %(employee)s
		AND on_hold = 0 AND is_active = 1 LIMIT 1 """,{ 
			"employee": filters.employee
		}, as_dict=True)

	return employees

def get_data(filters):
	#Initialize
	data = []
	employees = get_employees(filters)
	pay_from, pay_to = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to"])
	shift_map = get_shift_map()
	for emp in employees:
		timecard_list = get_timecard_list(emp.biometrics_id, pay_from, pay_to + datetime.timedelta(days=1))
		holidays = get_holiday_list(emp.company, emp.location, pay_from, pay_to)
		schedule = get_schedule(emp.name, pay_from, pay_to)
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
			entry['break'] = convert_secs(filters, entry['break'])
			entry['work'] = convert_secs(filters, entry['work'])
			entry['late'] = convert_secs(filters, entry['late'])
			entry['undertime'] = convert_secs(filters, entry['undertime'])
			entry['overtime'] = convert_secs(filters, entry['overtime'])
			data.append(entry)

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