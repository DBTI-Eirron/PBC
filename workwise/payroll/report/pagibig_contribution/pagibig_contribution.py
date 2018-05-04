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
		employee_amt = frappe.db.sql_list("""SELECT amount FROM `tabPayroll Register` WHERE
					pay_code = 'HDMF' 
					AND employee = %(employee)s 
					AND pay_period = %(period)s LIMIT 1""",{ 
				"employee": d.name,
				"period": filters.payroll_period
			})
		#frappe.throw(_("{0}").format(employee_amt))
		employer_amt = frappe.db.sql_list("""SELECT employer_amount FROM `tabPayroll Register`
					 pay_code = 'HDMF' 
					 AND employee = %(employee)s 
					 AND pay_period = %(period)s LIMIT 1""",{ 
				"employee": d.name,
				"period": filters.payroll_period
			})

		total = employee_amt + employer_amt
		row = [d.hdmf_no, "", "", d.last_name, d.first_name, d.name_extension, d.middle_name, "",  employee_amt, employer_amt, "",]

		data.append(row)

	return columns, data

def get_columns(employee_list):
	columns = [
		{
			"fieldname": "gov_no",
			"label": _("Pag-IBIG ID/RTN"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "account_no",
			"label": _("Account No"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "membership",
			"label": _("Membership Program"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "last_name",
			"label": _("Last name"),
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
			"fieldname": "name_extension",
			"label": _("Name Extension"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "middle_name",
			"label": _("Middle Name"),
			"fieldtype": "Data",
			"width": 150
		},

		{
			"fieldname": "percov",
			"label": _("PERCOV"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Float",
			"width": 100
		},		
		{
			"fieldname": "employer",
			"label": _("Employer"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "remarks",
			"label": _("Remarks"),
			"fieldtype": "Text",
			"width": 200
		},
	]

	return columns

def get_employees(filters):
	employees = frappe.db.sql("""SELECT *
	 	FROM tabEmployee
		WHERE company = %(company)s
		AND on_hold = 0
		AND is_active = 1 ORDER BY last_name, first_name""",{ 
			"company": filters.company
		}, as_dict=True)

	return employees
