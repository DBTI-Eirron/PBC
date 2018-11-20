# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	employee_list = get_employees(filters)

	columns = get_columns(employee_list)

	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list

	total_amount = 0.0	

	data = []
	for emp in employee_list:
		row = [emp.employee, emp.employee_name, emp.amount]
		total_amount += emp.amount
		data.append(row)
	data.append(["", "", total_amount])

	return columns, data

def get_columns(employee_list):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 160
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 260
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Float",
			"width": 160
		}
	]

	return columns

def get_employees(filters):
	from_date, to_date = frappe.db.get_value("Payroll Year", filters.year, ["from_date", "to_date"])
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql("""SELECT DISTINCT LE.employee, LE.employee_name, LE.payroll_year, LR.description, LR.amount 
			FROM `tabLast Pay Entry` LE JOIN `tabLast Pay Register` LR ON LE.`name` = LR.parent JOIN `tabEmployee` TE ON LE.employee = TE.`name` 
			WHERE LR.description = "Pro Rated 13th Month" 
			AND TE.company = %(company)s
			AND LE.payroll_year = %(year)s
			AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s)""", { 
				"year": filters.year,
				"company": filters.company,
				"user": cur_user
			}, as_dict=1)
	else:
		employees = frappe.db.sql("""SELECT DISTINCT LE.employee, LE.employee_name, LE.payroll_year, LR.description, LR.amount 
			FROM `tabLast Pay Entry` LE JOIN `tabLast Pay Register` LR ON LE.`name` = LR.parent JOIN `tabEmployee` TE ON LE.employee = TE.`name`  
			WHERE TE.company = %(company)s
			AND LE.payroll_year = %(year)s
			AND LR.description = "Pro Rated 13th Month" """, { 
				"year": filters.year,
				"company": filters.company,
			}, as_dict=1)

	return employees