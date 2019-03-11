# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	employee_list = get_employees(filters)
	
	if not employee_list:
		frappe.throw(_("No record found"))
		return columns, employee_list

	data = []

	for emp in employee_list:
		row = [emp.employee, emp.employee_name, emp.learning_session, emp.average_rating]

		data.append(row)

	return columns, data

def get_columns(filters):
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
		{
			"fieldname": "session",
			"label": _("Session"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "average_rating",
			"label": _("Average Rating"),
			"fieldtype": "Float",
			"width": 200
		},
	]

	return columns

def get_employees(filters):
	employees = frappe.db.sql(""" SELECT DISTINCT employee, employee_name, `learning_session`, average_rating FROM `tabLearning Session Evaluation` WHERE learning_event = %s AND company = %s AND docstatus = 1 """, (filters.event, filters.company), as_dict=True)

	return employees
