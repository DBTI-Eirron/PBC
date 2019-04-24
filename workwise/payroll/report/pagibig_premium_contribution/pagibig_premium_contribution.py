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
	HDMF_types = ["HDMFM", "HDMF", "HDMFE"]
	columns = get_columns(filters)

	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list

	HDMF_map = get_HDMF_map(filters, employee_list)

	final_employee, final_employer, final_total = 0, 0, 0

	data = []

	if filters.include_header:
		hdmf_id = frappe.db.get_value("Company", filters.company, "hdmf_id")
		address = frappe.db.sql_list("""SELECT DISTINCT(TA.`address_line1`) as address
			 FROM `tabDynamic Link` DL 
			 JOIN `tabAddress` TA WHERE DL.`parenttype` = "Address" 
			 AND DL.`link_doctype` = "Company" AND DL.`parent` = TA.`name` 
			 AND TA.`address_type` = "Registered" AND DL.`link_name` = %s LIMIT 1 """, filters.company)
		
		headers = [
			[
				"Employer ID", hdmf_id 
			],
			[
				"Employer Name", filters.company
			],
			[
				"Address", address[0] if address else ""
			],
			[
				"Employee ID", "Employee Name", "HDMF Number", "Employee", "Employer", "Total"
			],
		]

		for d in headers:
			data.append(d)

	for emp in employee_list:
		emp_cont = 0.00
		empr_cont = 0.00
		tot_cont = 0.00
		row = [emp.name, emp.full_name, emp.hdmf_no]
		result = []
		total_HDMF = 0
		for d in HDMF_types:
			HDMF_amount = flt(HDMF_map.get(emp.name, {}).get(d))
			total_HDMF += HDMF_amount
			result.append('{:,.2f}'.format(HDMF_amount))
		emp_cont = flt(result[0]) + flt(result[1])
		empr_cont = flt(result[2])
		tot_cont = flt(result[0]) + flt(result[1]) + flt(result[2])
		row.append('{:,.2f}'.format(emp_cont))
		row.append('{:,.2f}'.format(empr_cont))
		row.append('{:,.2f}'.format(tot_cont))

		if total_HDMF > 0:
			final_employee += flt(HDMF_map.get(emp.name, {}).get("HDMF")) + flt(HDMF_map.get(emp.name, {}).get("HDMFM"))
			final_employer += flt(HDMF_map.get(emp.name, {}).get("HDMFE"))
			final_total += total_HDMF
			row += ['{:,.2f}'.format(total_HDMF)]

			data.append(row)

	final = ["<b>Total: </b>","" , "", '{:,.2f}'.format(final_employee), '{:,.2f}'.format(final_employer), '{:,.2f}'.format(final_total)]
	data.append(final)

	return columns, data

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

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
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 220
		},
		{
			"fieldname": "hdmf_no",
			"label": _("HDMF Number"),
			"fieldtype": "Data",
			"width": 160
		},
		{
			"fieldname": "HDMF",
			"label": _("Employee"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "HDMFE",
			"label": _("Employer"),
			"fieldtype": "Currency",
			"width":120
		},
		{
			"fieldname": "total_HDMF",
			"label": _("Total"),
			"fieldtype": "Currency",
			"width": 100
		},
	]

	if filters.include_header:
		columns = [
			{
				"fieldname": "employee",
				"label": _(""),
				"fieldtype": "Data",
				"width": 100
			},
			{
				"fieldname": "employee_name",
				"label": _(""),
				"fieldtype": "Data",
				"width": 220
			},
			{
				"fieldname": "hdmf_no",
				"label": _(""),
				"fieldtype": "Data",
				"width": 160
			},
			{
				"fieldname": "HDMF",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "HDMFE",
				"label": _(""),
				"fieldtype": "Data",
				"width":120
			},
			{
				"fieldname": "total_HDMF",
				"label": _(""),
				"fieldtype": "Data",
				"width": 100
			},
		]

	return columns

def get_employees(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee as `name`, PR.employee_name as full_name, TE.hdmf_no  FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
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
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee as `name`, PR.employee_name as full_name, TE.hdmf_no FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
				WHERE PR.company = %(company)s 
				AND PR.posting_date >= %(from_date)s
				AND PR.posting_date <= %(to_date)s
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`) ORDER BY PR.employee_name """,{ 
				"company": filters.company,
				"from_date": filters.from_date,
				"to_date": filters.to_date
			}, as_dict=True)

	return employees

def get_HDMF_map(filters, employee_list):
	HDMF_details = frappe.db.sql(""" SELECT DISTINCT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
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
