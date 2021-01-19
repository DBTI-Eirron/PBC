# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _
from frappe.utils import cint, flt, getdate, cstr
import frappe

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
			"width": 140
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 340
		},
		{
			"fieldname": "balance",
			"label": _("Balance"),
			"fieldtype": "Data",
			"width": 100
		},
	]
	return columns

def get_result(filters):
	result = get_result(filters)

	return result

def get_result(filters):
	data = []
	total_bal = 0
	employees = get_employee(filters)
	cto = get_cto(employees, filters)
	cto_list = []

	for e in employees:
		if filters.employee:
			if e.name != filters.employee:
				continue

		balance = 0
		for c in cto:
			if e.name == c.employee:
				balance += c.balance
				cto_list.append({"Name": c.name, "Balance": balance})

		if filters.hide_zero:
			if balance == 0:
				continue
				
		total_bal += balance
		data.append({
			"employee_id": e.name,
			"employee_name": e.full_name,
			"balance": flt(balance, 3)
			})

	data.sort(key=lambda x: x.get('employee_name'))
	data.append({
		"employee_name": "Total",
		"balance": flt(total_bal, 3) 
		})
	#frappe.throw(_(cto_list))
	return data

def get_employee(filters):
	employee_list = frappe.db.sql("""SELECT name, full_name FROM `tabEmployee` WHERE company = %s ORDER BY `name`""",(filters.company), as_dict=True)

	return employee_list

def get_cto(emp, filters):
	cto_validity = frappe.db.get_single_value('Timekeeping Settings', 'cto_validity')
	if cto_validity > 0:
		cto_validity_condition = "AND `from_date` BETWEEN DATE_SUB(CURDATE(), INTERVAL "+cto_validity+" DAY) AND CURDATE()"
	else:
		cto_validity_condition = ""

	cto_zero = frappe.db.get_single_value('Timekeeping Settings', 'cto_zero_out')
	if cto_zero:
		cto_balance_condition = "AND YEAR(`from_date`) = YEAR(CURDATE())"
	else:
		cto_balance_condition = ""

	cto = frappe.db.sql("""SELECT total_balance as balance, `file_target_date`, `employee`, `name`, YEAR(`from_date`) FROM `tabCompensatory Time Off` 
		WHERE `type` = "File" AND `docstatus` = 1 AND `workflow_state` = "Approved" 
		AND `total_balance` > 0 {conditions}{cto_balance_con}""".format(conditions=cto_validity_condition, cto_balance_con=cto_balance_condition), as_dict=True)

	
	return cto