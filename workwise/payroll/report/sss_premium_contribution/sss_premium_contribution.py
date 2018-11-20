# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})

	employee_list = get_employees(filters)
	sss_types = ["SSS", "SSSE", "SSSC"]
	columns = get_columns(employee_list)

	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list

	sss_map = get_sss_map(filters, employee_list)

	final_employee, final_employer, final_ec, final_total = 0, 0, 0, 0

	data = []
	for emp in employee_list:
		row = [emp.name, emp.full_name, emp.sss_no]

		total_sss = 0
		for sss in sss_types:
			sss_amount = flt(sss_map.get(emp.name, {}).get(sss))
			total_sss += sss_amount
			row.append(sss_amount)

		if total_sss > 0:
			final_employee += flt(sss_map.get(emp.name, {}).get("SSS"))
			final_employer += flt(sss_map.get(emp.name, {}).get("SSSE"))
			final_ec += flt(sss_map.get(emp.name, {}).get("SSSC"))
			final_total += total_sss
			row += [total_sss]
			
			data.append(row)

	final = ["<b>Total: </b>","", "", final_employee, final_employer, final_ec, final_total]
	data.append(final)

	return columns, data

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
			"fieldname": "sss_no",
			"label": _("SSS Number"),
			"fieldtype": "Data",
			"width": 160
		},
		{
			"fieldname": "SSS",
			"label": _("Employee"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "SSSE",
			"label": _("Employer"),
			"fieldtype": "Float",
			"width":120
		},
		{
			"fieldname": "SSSC",
			"label": _("Contribution"),
			"fieldtype": "Float",
			"width":120
		},
		{
			"fieldname": "total_sss",
			"label": _("Total"),
			"fieldtype": "Float",
			"width": 100
		},
	]

	return columns

def get_employees(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee as `name`, PR.employee_name as full_name, TE.sss_no FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
				WHERE PR.company = %(company)s 
				AND PR.posting_date >= %(from_date)s
				AND PR.posting_date <= %(to_date)s
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s) 
				ORDER BY PR.employee_name """,{ 
				"company": filters.company,
				"from_date": filters.from_date,
				"to_date": filters.to_date,
				"user": frappe.session.user
			}, as_dict=True)
	else:
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee as `name`, PR.employee_name as full_name, TE.sss_no FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
				WHERE PR.company = %(company)s 
				AND PR.posting_date >= %(from_date)s
				AND PR.posting_date <= %(to_date)s
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`) ORDER BY PR.employee_name """,{ 
				"company": filters.company,
				"from_date": filters.from_date,
				"to_date": filters.to_date
			}, as_dict=True)

	return employees

def get_sss_map(filters, employee_list):
	sss_details = frappe.db.sql(""" SELECT DISTINCT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		WHERE employee in (%s) GROUP BY PRE.`name` """ %
		', '.join(['%s']*len(employee_list)), tuple([emp.name for emp in employee_list]), as_dict=1)

	sss_map = {}
	for d in sss_details:
		if getdate(filters.from_date) <= getdate(d.posting_date) <= getdate(filters.to_date):
			sss_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
			if sss_map[d.employee][d.pay_code]:
				sss_map[d.employee][d.pay_code] += flt(d.amount, 2)
			else:
				sss_map[d.employee][d.pay_code] = flt(d.amount, 2)

	return sss_map