# Copyright (c) 2013, HDI Systech and contributors
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
			"fieldtype": "Link",
			"options": "Employee",
			"width": 130
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "date_of_retirement",
			"label": _("Date of Retirement"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "retirement_type",
			"label": _("Retirement Type"),
			"fieldtype": "Data",
			"width": 130
		},
	]

	return columns

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_data(filters):
	#Initialize
	data = []

	employees = get_employees(filters)
	for emp in employees:
		movements = frappe.db.sql(""" SELECT `employee`,`employee_name`,`effective_on`,`retirement_type` FROM `tabEmployee Movement` WHERE `docstatus` = 1 AND `employee` = %s AND `effective_on` > CURRENT_DATE """, (emp.name),as_dict=True)
		for movement in movements:
			entry = {
				"employee_id": movement.employee,
				"employee_name": movement.employee_name,
				"date_of_retirement": movement.effective_on,
				"retirement_type": movement.retirement_type,
			}

			data.append(entry)

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)
	return result

def get_employees(filters):
	register = frappe.db.sql("""SELECT `name`, full_name FROM `tabEmployee` 
		WHERE company = %s """, (filters.company), as_dict=1)

	return register
