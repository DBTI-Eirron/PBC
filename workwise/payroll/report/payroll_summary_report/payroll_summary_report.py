# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import get_work, get_break

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	validate_filters(filters)

	employee_list = get_employees(filters)
	columns, income_types, deduction_types = get_columns(employee_list)

	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list

	income_map = get_income_map(filters, employee_list)
	deduction_map = get_deduction_map(filters, employee_list)

	data = []
	for emp in employee_list:

		row = [emp.name, emp.full_name]

		total_income = 0
		for income in income_types:
			income_amount = flt(income_map.get(emp.name, {}).get(income), 2)
			total_income += flt(income_amount, 2)
			row.append(income_amount)

		total_deduction = 0
		for deduction in deduction_types:
			deduction_amount = flt(deduction_map.get(emp.name, {}).get(deduction), 2)
			total_deduction += flt(deduction_amount, 2)
			row.append(deduction_amount)

		total_payroll = flt(total_income, 2) - flt(total_deduction, 2)
		row += [total_income, total_deduction, total_payroll]

		data.append(row)

	return columns, data

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

def get_columns(employee_list):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 200
		},
	]

	if employee_list:
		income_types = frappe.db.sql_list(""" SELECT code
			FROM `tabTransaction Type` WHERE `type` = 'Income' ORDER BY code """)

		deduction_types = frappe.db.sql_list(""" SELECT code
			FROM `tabTransaction Type` WHERE `type` = 'Deduction' ORDER BY code""")

	for pay_code in income_types:
		pay_title = frappe.db.sql("""SELECT `title` FROM `tabTransaction Type` WHERE code = %(pay_code)s  """,{
			"pay_code": pay_code
		})

		columns.append({			
			"fieldname": pay_code,
			"label": pay_title,
			"fieldtype": "Data",
			"width": 100
		})

	for pay_code in deduction_types:
		pay_title = frappe.db.sql("""SELECT `title` FROM `tabTransaction Type` WHERE code = %(pay_code)s """,{
			"pay_code": pay_code
		})

		columns.append({			
			"fieldname": pay_code,
			"label": pay_title,
			"fieldtype": "Data",
			"width": 100
		})

	columns += [
		{
			"fieldname": "total_income",
			"label": _("Total Income"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "total_deduction",
			"label": _("Total Deduction"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "total_payroll",
			"label": _("Total Payroll"),
			"fieldtype": "Float",
			"width": 100
		},
	]

	return columns, income_types, deduction_types

def get_employees(filters):
	employees = frappe.db.sql("""SELECT *
	 	FROM tabEmployee
		WHERE company = %(company)s
		AND on_hold = 0
		AND is_active = 1 ORDER BY last_name, first_name""",{ 
			"company": filters.company
		}, as_dict=True)

	return employees

def get_income_map(filters, employee_list):
	income_details = frappe.db.sql("""SELECT employee, pay_code, pay_date, amount
		FROM `tabPayroll Register` WHERE employee in (%s) group by `name` """ %
		', '.join(['%s']*len(employee_list)), tuple([emp.name for emp in employee_list]), as_dict=1)

	income_map = {}
	for d in income_details:
		if getdate(filters.from_date) <= getdate(d.pay_date) <= getdate(filters.to_date):
			income_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
			if income_map[d.employee][d.pay_code]:
				income_map[d.employee][d.pay_code] += flt(d.amount, 2)
			else:
				income_map[d.employee][d.pay_code] = flt(d.amount, 2)

		
	return income_map

def get_deduction_map(filters, employee_list):
	deduction_details = frappe.db.sql("""SELECT employee, pay_code, pay_date, amount
		FROM `tabPayroll Register` WHERE employee in (%s) group by `name` """ %
		', '.join(['%s']*len(employee_list)), tuple([emp.name for emp in employee_list]), as_dict=1)

	deduction_map = {}
	for d in deduction_details:
		if getdate(filters.from_date) <= getdate(d.pay_date) <= getdate(filters.to_date):
			deduction_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
			if deduction_map[d.employee][d.pay_code]:
				deduction_map[d.employee][d.pay_code] += flt(d.amount, 2)
			else: 
				deduction_map[d.employee][d.pay_code] = flt(d.amount, 2)

	return  deduction_map