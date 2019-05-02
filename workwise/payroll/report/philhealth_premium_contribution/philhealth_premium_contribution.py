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
	PHIC_types = ["PHIC", "PHICE"]
	columns = get_columns(employee_list)

	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list

	PHIC_map = get_PHIC_map(filters, employee_list)

	final_employee, final_employer, final_total = 0, 0, 0

	data = []
	for emp in employee_list:
		row = [emp.name, emp.full_name, emp.phic_no]

		total_PHIC = 0
		for PHIC in PHIC_types:
			PHIC_amount = flt(PHIC_map.get(emp.name, {}).get(PHIC))
			total_PHIC += PHIC_amount
			row.append('{:,.2f}'.format(PHIC_amount))

		if total_PHIC > 0:
			final_employee += flt(PHIC_map.get(emp.name, {}).get("PHIC"))
			final_employer += flt(PHIC_map.get(emp.name, {}).get("PHICE"))
			final_total += total_PHIC
			row += ['{:,.2f}'.format(total_PHIC)]

			data.append(row)

	final = ["<b>Total: </b>","", "", '{:,.2f}'.format(final_employee), '{:,.2f}'.format(final_employer), '{:,.2f}'.format(final_total)]
	data.append(final)

	i = 0
	for x in data:
		if data[i][5] <= 0.0:
			data.pop(i)
		i += 1

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
			"fieldname": "phic_no",
			"label": _("PHIC Number"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "PHIC",
			"label": _("Employee"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "PHICE",
			"label": _("Employer"),
			"fieldtype": "Currency",
			"width":120
		},
		{
			"fieldname": "total_PHIC",
			"label": _("Total"),
			"fieldtype": "Currency",
			"width": 100
		},
	]

	return columns

def get_employees(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee as `name`, PR.employee_name as full_name, TE.phic_no FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
				WHERE PR.company = %(company)s 
				AND PR.posting_date >= %(from_date)s
				AND PR.posting_date <= %(to_date)s
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s)
				GROUP BY PR.employee
				ORDER BY PR.employee_name """,{ 
				"company": filters.company,
				"from_date": filters.from_date,
				"to_date": filters.to_date,
				"user": frappe.session.user
			}, as_dict=True)
	else:
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee as `name`, PR.employee_name as full_name, TE.phic_no FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
				WHERE PR.company = %(company)s 
				AND PR.posting_date >= %(from_date)s
				AND PR.posting_date <= %(to_date)s
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`) 
				GROUP BY PR.employee
				ORDER BY PR.employee_name """,{ 
				"company": filters.company,
				"from_date": filters.from_date,
				"to_date": filters.to_date
			}, as_dict=True)

	return employees

def get_PHIC_map(filters, employee_list):
	PHIC_details = frappe.db.sql(""" SELECT DISTINCT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		WHERE employee in (%s) GROUP BY PRE.`name` """ %
		', '.join(['%s']*len(employee_list)), tuple([emp.name for emp in employee_list]), as_dict=1)

	PHIC_map = {}
	for d in PHIC_details:
		if getdate(filters.from_date) <= getdate(d.posting_date) <= getdate(filters.to_date):
			PHIC_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
			if PHIC_map[d.employee][d.pay_code]:
				PHIC_map[d.employee][d.pay_code] += flt(d.amount, 2)
			else:
				PHIC_map[d.employee][d.pay_code] = flt(d.amount, 2)

	return PHIC_map