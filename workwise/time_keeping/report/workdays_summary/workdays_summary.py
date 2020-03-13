# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee_id",
			"label": _("Employee ID"),
			"fieldtype": "Data",
			"width": 80
		},
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Data",
			"width": 250
		},
		{
			"fieldname": "total_workdays",
			"label": _("Work Days"),
			"fieldtype": "Float",
			"width": 140
		},
		{
			"fieldname": "total_restday",
			"label": _("Rest days"),
			"fieldtype": "Float",
			"width": 140
		},
		{
			"fieldname": "total_presentdays",
			"label": _("Present Days"),
			"fieldtype": "Float",
			"width": 140
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

	if not filters.company:
		frappe.throw("Filter company is Required")

def get_data(filters):
	#Initialize
	data = []
	employee_list = get_employees(filters)
	attendance_register= get_period(filters)
	t_work, t_rest, t_present = 0, 0, 0
	if employee_list:
		for e in employee_list:
			if filters.employee:
				if e.name != filters.employee:
					continue
			workdays_list = {}
			total_workdays, total_restdays, total_presentdays, absent_days = 0, 0, 0, 0
			for ar in attendance_register:
				if e.name == ar.employee:
					if ar.is_restday:
						total_restdays += 1
					else:
						total_workdays +=1
						if ar.is_halfday:
							absent_days += .5
						else:
							if ar.is_absent:
								absent_days += 1
							if ar.is_lwop:
								if not ar.work:
									absent_days += 1
								else:
									absent_days += .5

			total_presentdays = total_workdays - absent_days 
			if total_workdays == 0 and total_restdays == 0 and total_presentdays == 0:
				continue
			workdays_list = {
				'employee_id': e.name,
				'employee': e.full_name,
				'total_workdays': total_workdays,
				'total_restday': total_restdays,
				'total_presentdays': total_presentdays,
				}
			data.append(workdays_list)
			t_work += total_workdays
			t_rest += total_restdays
			t_present += total_presentdays
	if data:
		data = sorted(data, key = lambda i: i['employee'])
		totals = {
			'employee': '<b> Totals </b>',
			'total_workdays': t_work,
			'total_restday': t_rest,
			'total_presentdays': t_present,
			}
		data.append(totals)

	return data

def get_employees(filters):
	employees = frappe.db.sql("""SELECT `name`, full_name FROM `tabEmployee` WHERE `company` = %(company)s
		AND is_active = 1""",{ 
			"company": filters.company
		}, as_dict=True)

	return employees

def get_period(filters):
	date_from, date_to = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to"])
	period = frappe.db.sql("""SELECT `employee`, work, is_restday, is_absent, is_lwop, is_halfday FROM `tabAttendance Register` WHERE `target_date` BETWEEN %s AND %s""", (date_from, date_to), as_dict=True)

	return period

def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)
	return result