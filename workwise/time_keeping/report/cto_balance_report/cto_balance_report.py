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

	for e in employees:
		if filters.employee:
			if e.name != filters.employee:
				continue

		balance = 0
		for c in cto:
			if e.name == c.employee:
				balance += c.balance

		if filters.hide_zero:
			if balance == 0:
				continue
				
		total_bal += balance
		data.append({
			"employee_id": e.name,
			"employee_name": e.full_name,
			"balance": balance
			})

	data.sort(key=lambda x: x.get('employee_name'))
	data.append({
		"employee_name": "Total",
		"balance": total_bal
		})
	return data

def get_employee(filters):
	employee_list = frappe.db.sql("""SELECT name, full_name FROM `tabEmployee` WHERE company = %s ORDER BY `name`""",(filters.company), as_dict=True)

	return employee_list

def get_cto(emp, filters):
	cto_validity = frappe.db.get_single_value('Timekeeping Settings', 'cto_validity')
	if cto_validity > 0:
		cto_validity_condition = " AND (CTO.`file_target_date` BETWEEN CURDATE() AND DATE_SUB(CURDATE(), INTERVAL -"+str(int(cto_validity))+" DAY)) "
	else:
		cto_validity_condition = ""

	cto = frappe.db.sql("""SELECT CTO.`name`, CTO.`balance`, CTO.`file_target_date`, CTO.`employee` FROM `tabCompensatory Time Off` CTO INNER JOIN `tabEmployee` E ON CTO.`employee` = E.`name`
			WHERE CTO.`type` = "File" AND CTO.`docstatus` = 1 AND CTO.`workflow_state` = "Approved" AND E.`company` = %(company)s
			AND CTO.`balance` > 0 {conditions} ORDER BY CTO.`file_target_date` ASC""".format(conditions=cto_validity_condition),{
				"cto_validity": cto_validity,
				"company": filters.company
				}, as_dict=True)
	return cto
