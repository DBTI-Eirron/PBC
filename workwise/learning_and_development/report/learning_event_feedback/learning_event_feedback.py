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
		fd = ""
		row = [emp.employee, emp.employee_name]

		feedback = frappe.db.sql("""SELECT feedback FROM `tabLearning Feedback` WHERE docstatus = 1 AND `learning_event` = %s AND employee = %s """, (filters.training_name, emp.employee), as_dict=True)
		for f in feedback:
			if f.feedback:
				fd = f.feedback
			else:
				fd = ""
		row.append(fd)
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
			"fieldname": "feedback",
			"label": _("Feedback"),
			"fieldtype": "Data",
			"width": 300
		},
	]

	return columns

def get_employees(filters):
	employees = frappe.db.sql("""SELECT `employee`, employee_name	FROM `tabLearning Evaluation`
		WHERE docstatus = 1 AND event_type = "Learning Event" AND event = %s """, (filters.training_name), as_dict=True)

	return employees

def get_conditions(filters):
	conditions = []
	if filters.get("training_name"):
		conditions.append("`event`=%(training_name)s")

	if filters.get("employee"):
		conditions.append("`employee`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 