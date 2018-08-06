# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	validate_filters(filters)

	employee_list = get_employees(filters)
	HDMF_types = ["HDMF", "HDMFE"]
	columns = get_columns(employee_list)

	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list

	HDMF_map = get_HDMF_map(filters, employee_list)

	data = []
	for emp in employee_list:
		row = [emp.name, emp.full_name]

		total_HDMF = 0
		for HDMF in HDMF_types:
			HDMF_amount = flt(HDMF_map.get(emp.name, {}).get(HDMF))
			total_HDMF += HDMF_amount
			row.append(HDMF_amount)

		row += [total_HDMF]

		data.append(row)

	return columns, data

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

def get_columns(employee_list):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 220
		},
		{
			"fieldname": "HDMF",
			"label": _("Employee"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "HDMFE",
			"label": _("Employer"),
			"fieldtype": "Float",
			"width":120
		},
		{
			"fieldname": "total_HDMF",
			"label": _("Total"),
			"fieldtype": "Float",
			"width": 100
		},
	]

	return columns

def get_employees(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql("""SELECT *
		 	FROM tabEmployee
			WHERE sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
				INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`
				WHERE SU.allow_user = %(user)s)
			AND company = %(company)s
			AND on_hold = 0
			AND is_active = 1 ORDER BY last_name, first_name""",{ 
				"company": filters.company,
				"user": frappe.session.user
			}, as_dict=True)
	else:
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

def get_HDMF_map(filters, employee_list):
	HDMF_details = frappe.db.sql(""" SELECT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		WHERE employee in (%s) GROUP BY PRE.`name` """ %
		', '.join(['%s']*len(employee_list)), tuple([emp.name for emp in employee_list]), as_dict=1)

	HDMF_map = {}
	for d in HDMF_details:
		if getdate(filters.from_date) <= getdate(d.posting_date) <= getdate(filters.to_date):
			HDMF_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
			if HDMF_map[d.employee][d.pay_code]:
				HDMF_map[d.employee][d.pay_code] += flt(d.amount, 2)
			else:
				HDMF_map[d.employee][d.pay_code] = flt(d.amount, 2)

	return HDMF_map
