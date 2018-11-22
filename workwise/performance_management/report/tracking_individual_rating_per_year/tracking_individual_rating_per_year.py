# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, getdate, cstr, add_to_date, get_datetime
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	employee_list = get_employees(filters)

	if not employee_list:
		frappe.throw(_("No record found"))
		return columns, employee_list

	data = []
	pay_year = frappe.db.sql("""SELECT `name` FROM `tabPayroll Year` WHERE docstatus = 1 """, as_dict=True)
	for emp in employee_list:
		row = [emp.appraisee, emp.appraisee_name]
		for d in pay_year:
			date_from, date_to = frappe.db.get_value("Payroll Year", d.name, ["from_date", "to_date"])

			appraisal = frappe.db.sql("""SELECT DISTINCT * FROM `tabAppraisal` WHERE appraisee = %(employee)s AND docstatus = 1 AND (from_date BETWEEN %(from_date)s AND %(to_date)s) AND (to_date BETWEEN %(from_date)s AND %(to_date)s) """,{ 
				"from_date": date_from,
				"to_date": date_to,
				"employee": emp.appraisee
			}, as_dict=True)

			i = 0
			tot_score = 0
			total_score = 0
			for a in appraisal:
				tot_score += a.total_score
				i += 1

			if i == 0:
				i = 1
				
			total_score = flt(tot_score, 2) / i

			row.append(flt(total_score, 2))

		data.append(row)

	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 150
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 180
		},
	]

	pay_year = frappe.db.sql("""SELECT `name` FROM `tabPayroll Year` WHERE docstatus = 1 """, as_dict=True)
	if pay_year:
		for d in pay_year:
			columns += [
				{
					"fieldname": d.name,
					"label": _(d.name),
					"fieldtype": "Data",
					"width": 120
				},
			]

	return columns

def get_employees(filters):
	employees = frappe.db.sql("""SELECT DISTINCT `appraisee`, appraisee_name FROM `tabAppraisal` WHERE docstatus = 1 AND company = %s """, (filters.company), as_dict=True)

	return employees