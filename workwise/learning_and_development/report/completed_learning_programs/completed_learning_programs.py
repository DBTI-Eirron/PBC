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
	row = []
	has_course = frappe.db.sql("""SELECT DISTINCT parent, employee_name FROM `tabLearning Participants` WHERE `parenttype` = "Learning Event" AND `employee` = %s """, (filters.employee), as_dict=True)
	for hc in has_course:
		event = frappe.db.sql("""SELECT DISTINCT learning_program FROM `tabLearning Event` WHERE `name` = %s AND event_status = "Completed" """, (hc.parent), as_dict=True)
		for e in event:
			row = [e.learning_program]

			data.append(row)

	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "program",
			"label": _("Learning Program"),
			"fieldtype": "Link",
			"options": "Learning Program",
			"width": 250
		},
	]

	return columns

def get_employees(filters):
	register = frappe.db.sql("""SELECT `name`, full_name FROM `tabEmployee` 
		WHERE company = %(company)s {conditions}""".format(conditions=get_conditions(filters)), filters, as_dict=1)

	return register

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")

	if filters.get("department"):
		conditions.append("department=%(department)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 