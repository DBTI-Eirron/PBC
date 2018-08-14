# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

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
	grand_total = 0
	total_row= ["",""]
	for income in income_types:
		total_row.append("")

	for deduction in deduction_types:
		total_row.append("")

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
		if total_payroll < 0:
			total_payroll = 0
		row += [total_income, total_deduction, total_payroll]
		grand_total += total_payroll
		
		data.append(row)
	total_row += ["", "", grand_total]
	data.append(total_row)

	return columns, data

def validate_filters(filters):
	if filters.period:
		period_company = frappe.db.get_value("Payroll Period", filters.period, 'company')
		if period_company != filters.company:
			frappe.throw(_("Period {0} Does not belong to company {1}").format(filters.period, filters.company))

	if filters.employee:
		emp_company = frappe.db.get_value("Employee", filters.employee, 'company')
		if emp_company != filters.company:
			frappe.throw(_("Employee {0} Does not belong to company {1}").format(filters.employee, filters.company))

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
		pay_title = frappe.db.get_value("Transaction Type", pay_code, 'title')
		columns.append({			
			"fieldname": pay_code,
			"label": pay_title,
			"fieldtype": "Float",
			"width": 100
		})

	for pay_code in deduction_types:
		pay_title = frappe.db.get_value("Transaction Type", pay_code, 'title')
		columns.append({			
			"fieldname": pay_code,
			"label": pay_title,
			"fieldtype": "Float",
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
	employees = frappe.db.sql("""SELECT `name`, full_name, first_name, middle_name, last_name, department	FROM tabEmployee
		WHERE company = %(company)s {conditions}
		AND on_hold = 0 AND is_active = 1 ORDER BY last_name, first_name""".format(conditions=get_conditions(filters)), filters, as_dict=1)

	return employees

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")
		
	if filters.get("department"):
		conditions.append("department=%(department)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 

def get_income_map(filters, employee_list):
	income_details = frappe.db.sql("""SELECT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		WHERE PR.period = %s AND employee in (%s) GROUP BY PRE.`name` """ %
		('%s',', '.join(['%s']*len(employee_list))), tuple([filters.payroll_period] + [emp.name for emp in employee_list]), as_dict=1)

	income_map = {}
	for d in income_details:
		income_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
		if income_map[d.employee][d.pay_code]:
			income_map[d.employee][d.pay_code] += flt(d.amount, 8)
		else:
			income_map[d.employee][d.pay_code] = flt(d.amount, 8)

	return income_map

def get_deduction_map(filters, employee_list):
	deduction_details = frappe.db.sql("""SELECT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		WHERE PR.period = %s AND employee in (%s) GROUP BY PRE.`name` """ %
		('%s',', '.join(['%s']*len(employee_list))), tuple([filters.payroll_period] + [emp.name for emp in employee_list]), as_dict=1)

	deduction_map = {}
	for d in deduction_details:
		deduction_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
		if deduction_map[d.employee][d.pay_code]:
			deduction_map[d.employee][d.pay_code] += flt(d.amount, 8)
		else: 
			deduction_map[d.employee][d.pay_code] = flt(d.amount, 8)

	return  deduction_map