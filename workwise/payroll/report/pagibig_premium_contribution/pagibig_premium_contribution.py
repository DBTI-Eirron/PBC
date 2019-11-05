# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_decimal_by_2, format_decimal_by_2_align_right, format_decimal_by_2_align_right_negative
from frappe import _, msgprint
from operator import itemgetter

def execute(filters=None):
	columns = get_columns(filters)
	transaction_type = ['HDMF', 'HDMFE']
	employee_list, gov_map = get_employees(filters,transaction_type)
	final_employee, final_employer, final_total = 0, 0, 0

	data = []
	entries = []
	if filters.include_header:
		hdmf_id = frappe.db.get_value("Company", filters.company, "hdmf_id")
		address = frappe.db.sql_list("""SELECT DISTINCT(TA.`address_line1`) as address
			 FROM `tabDynamic Link` DL 
			 JOIN `tabAddress` TA WHERE DL.`parenttype` = "Address" 
			 AND DL.`link_doctype` = "Company" AND DL.`parent` = TA.`name` 
			 AND TA.`address_type` = "Registered" AND DL.`link_name` = %s LIMIT 1 """, filters.company)
		
		data += [
			{
				"employee": "Employer ID",
				"employee_name": hdmf_id,
			},
			{
				"employee": "Employer Name", 
				"employee_name": filters.company
			},
			{
				"employee": "Address", 
				"employee_name": address[0] if address else ""
			},
			{
				"employee": "Employee ID", 
				"employee_name": "Employee Name", 
				"hdmf_no": "HDMF Number",
				"HDMF": "Employee",
				"HDMFE": "Employer",
				"total_HDMF": "Total"
			},
		]

	for emp in gov_map:
		row = {
			"employee": gov_map[emp]['employee'], 
			"employee_name": gov_map[emp]['full_name'], 
			"hdmf_no": gov_map[emp]['hdmf_no'],
			"total_HDMF": "Total"
		}

		hdmf_total = 0
		for trans in transaction_type:
			sss_amount = gov_map[emp][trans]
			hdmf_total += sss_amount
			row[trans] = sss_amount

		if hdmf_total > 0:
			final_employee += flt(gov_map[emp]["HDMF"])
			final_employer += flt(gov_map[emp]["HDMFE"])
			final_total += hdmf_total
			row['total_HDMF'] = format_decimal_by_2(hdmf_total)
		entries.append(row)

	for ent in sorted(entries, key = lambda k:k['employee_name']):
		data.append(ent)
	
	#Total
	data.append({
		"employee": "<b>Total: </b>",
		"employee_name": "",
		"hdmf_no": "",
		"HDMF": format_decimal_by_2(final_employee),
		"HDMFE": format_decimal_by_2(final_employer),
		"total_HDMF": format_decimal_by_2(final_total),
	})

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

def get_employees(filters,transaction_type):
	employees = frappe.db.sql("""SELECT PRE.pay_code, PRE.amount, PR.posting_date, PR.employee as `name`, PR.employee_name as full_name, TE.hdmf_no
		FROM `tabPayroll Register Entries` PRE
		INNER JOIN `tabPayroll Register` PR ON PRE.`parent` = PR.`name`
		INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		WHERE PRE.pay_code IN ('"""+"','".join(str(e) for e in transaction_type)+"""') 
		AND PR.company = %(company)s 
		AND PR.posting_date BETWEEN %(from_date)s AND %(to_date)s
		{conditions}
		ORDER BY PR.employee_name""".format(conditions=get_conditions(filters)),{ 
		"company": filters.company,
		"from_date": filters.from_date,
		"to_date": filters.to_date
	}, as_dict=True)
	if not employees:
		frappe.throw(_("No Records Found"))

	type_list = {}
	for t in transaction_type:
		type_list.update({t:0.0})

	gov_map = {}
	for d in employees:
		if d.name not in gov_map:
			type_list.update({"full_name":d.full_name,"hdmf_no":d.hdmf_no,"employee":d.name})
			gov_map.setdefault(d.name, frappe._dict(type_list))
		gov_map[d.name][d.pay_code] += flt(d.amount)
	return employees, gov_map


def get_conditions(filters):
	conditions = []
	if frappe.session.user != "Administrator":
		conditions.append(_("TE.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = '{0}' )").format(frappe.session.user))

	if filters.period_group:
		conditions.append(_("TE.`period_group` = '{0}'").format(filters.period_group))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

