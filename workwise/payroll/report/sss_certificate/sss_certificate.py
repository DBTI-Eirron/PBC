# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	if not filters: filters = frappe._dict({})


	employee_list = get_employees(filters)
	columns = get_columns(employee_list)

	if not employee_list:
		frappe.msgprint(_("No record found"))
		return columns, employee_list

	data = []
	for d in employee_list:
		employee_amt = frappe.db.sql_list("""SELECT amount FROM `tabPayroll Register` WHERE source = 'Employee' 
					AND pay_code = 'SSS' 
					AND employee = %(employee)s 
					AND pay_period = %(period)s LIMIT 1""",{ 
				"employee": d.name,
				"period": filters.payroll_period
			})
		#frappe.throw(_("{0}").format(employee_amt))
		employer_amt = frappe.db.sql_list("""SELECT employer_amount FROM `tabPayroll Register` WHERE source = 'Employee'
					 AND pay_code = 'SSS' 
					 AND employee = %(employee)s 
					 AND pay_period = %(period)s LIMIT 1""",{ 
				"employee": d.name,
				"period": filters.payroll_period
			})

		compensation = frappe.db.sql_list("""SELECT compensation FROM `tabPayroll Register` WHERE source = 'Employee'
					 AND pay_code = 'SSS' 
					 AND employee = %(employee)s 
					 AND pay_period = %(period)s LIMIT 1""",{ 
				"employee": d.name,
				"period": filters.payroll_period
			})

		total = employee_amt + employer_amt
		row = [d.name, d.full_name, d.sss_no, employee_amt, employer_amt, compensation, total]

		data.append(row)

	return columns, data

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
		{
			"fieldname": "sss_no",
			"label": _("SSS No"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "employee_amt",
			"label": _("EE"),
			"fieldtype": "Float",
			"width": 200
		},
		{
			"fieldname": "employer_amt",
			"label": _("ER"),
			"fieldtype": "Float",
			"width": 200
		},
		{
			"fieldname": "ec",
			"label": _("EC"),
			"fieldtype": "Float",
			"width": 200
		},
		{
			"fieldname": "date_paid",
			"label": _("Date Paid"),
			"fieldtype": "Float",
			"width": 200
		},
	]

	return columns

def get_employees(filters):
	employees = frappe.db.sql("""SELECT *
	 	FROM tabEmployee
		WHERE company = %(company)s
		AND `name` = %(employee)s
		AND on_hold = 0
		AND is_active = 1 ORDER BY last_name, first_name LIMIT 1""",{ 
			"company": filters.company,
			"employee": filters.employee
		}, as_dict=True)

	return employees
