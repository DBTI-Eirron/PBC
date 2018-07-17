# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime, dateutil
from datetime import date  
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100
		},
		{
			"fieldname": "last_name",
			"label": _("Last Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "first_name",
			"label": _("First Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "full_name",
			"label": _("Full Name"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "birthday",
			"label": _("Birthday"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "gender",
			"label": _("Gender"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "area",
			"label": _("Area"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "religion",
			"label": _("Religion"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "position_title",
			"label": _("Position"),
			"fieldtype": "Data",
			"width": 150
		},
	]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_employees(filters):
	employees = frappe.db.sql("""SELECT *
		FROM tabEmployee
		WHERE sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
			INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
		AND company = %(company)s
		AND on_hold = 0
		AND is_active = 1 ORDER BY last_name, first_name""",{ 
			"company": filters.company
		}, as_dict=True)

	return employees

def get_data(filters):
	data = []
	employees = get_employees(filters)

	for emp in employees: 
		data.append(emp)

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = {
			"employee": d.get("name"),
			"last_name": d.get("last_name"),
			"first_name": d.get("first_name"),
			"full_name": d.get("full_name"),
			"birthday": d.get("birthday"),
			"gender": d.get("gender"),
			"area": d.get("area"),
			"religion": d.get("religion"),
			"position_title": d.get("position_title"),
		}
		
		result.append(row)

	return result