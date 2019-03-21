# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _, msgprint

def execute(filters=None):
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):
	columns = [
		{
			"fieldname": "hdmf_no",
			"label": _("Pad-IBIG ID"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120
		},
		{
			"fieldname": "last_name",
			"label": _("Last Name"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "first_name",
			"label": _("First Name"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "middle_name",
			"label": _("Middle Name"),
			"fieldtype": "Data",
			"width": 120
		},
		
		{
			"fieldname": "HDMF",
			"label": _("Employee Contribution"),
			"fieldtype": "Data",
			"width": 160
		},
		{
			"fieldname": "HDMFE",
			"label": _("Employer Contribution"),
			"fieldtype": "Data",
			"width":160
		},
		{
			"fieldname": "tin",
			"label": _("TIN"),
			"fieldtype": "Data",
			"width":120
		},
		{
			"fieldname": "birthdate",
			"label": _("Birth Date"),
			"fieldtype": "Data",
			"width":120
		},
	]

	if filters.include_header:
		columns = [
			{
				"fieldname": "hdmf_no",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "employee",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "last_name",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "first_name",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "middle_name",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "HDMF",
				"label": _(""),
				"fieldtype": "Data",
				"width": 160
			},
			{
				"fieldname": "HDMFE",
				"label": _(""),
				"fieldtype": "Data",
				"width":160
			},
			{
				"fieldname": "tin",
				"label": _(""),
				"fieldtype": "Data",
				"width":120
			},
			{
				"fieldname": "birthdate",
				"label": _(""),
				"fieldtype": "Data",
				"width":120
			},
		]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_data(filters):
	#Initialize
	data = []

	if not filters: filters = frappe._dict({})
	validate_filters(filters)

	employee_list = get_employees(filters)
	HDMF_types = ["HDMF", "HDMFE"]
	HDMF_map = get_HDMF_map(filters, employee_list)

	if filters.include_header:
		employer_name = ""
		address = ""
		zip_code = ""
		employer_type = ""
		contact = ""
		br_code = ""
		hdmf_id = ""
		payment_type = ""

		company = frappe.db.sql("""SELECT * FROM tabCompany WHERE `name` = %s LIMIT 1""",(filters.company), as_dict=True)
		if company:
			for d in company:
				hdmf_id = d.hdmf_id

		company_address = frappe.db.sql(""" SELECT DISTINCT TA.`address_line1`, TA.`pincode`, TA.`address_type` 
			FROM `tabDynamic Link` DL JOIN `tabAddress` TA 
			WHERE DL.`parenttype` = "Address" 
			AND DL.`link_doctype` = "Company" 
			AND DL.`parent` = TA.`name` 
			AND TA.`address_type` = "Registered" 
			AND DL.`link_name` = %s """, (filters.company), as_dict=1)
		if company_address:
			for com in company_address:
				address = com.address_line1
				zip_code = com.pincode

		company_contact = frappe.db.sql(""" SELECT DISTINCT TC.`phone` 
			FROM `tabContact` TC JOIN `tabDynamic Link` DL 
			WHERE DL.`parenttype` = "Contact" 
			AND DL.`link_doctype` = "Company" 
			AND DL.`link_name` = %s LIMIT 1""", (filters.company), as_dict=1)
		if company_contact:
			for con in company_contact:
				contact = con.phone

		report_columns = {
			"hdmf_no": "Employer's Name: ",
			"employee": filters.company,
			"last_name": "",
			"first_name": "",
			"middle_name": "Contact Number: ",
			"HDMF": contact,
			"HDMFE": "",
			"tin": "",
			"birthdate": "",
		}
		data.append(report_columns)

		report_columns = {
			"hdmf_no": "Address: ",
			"employee": address,
			"last_name": "",
			"first_name": "",
			"middle_name": "",
			"HDMF": "",
			"HDMFE": "",
			"tin": "",
			"birthdate": "",
		}
		data.append(report_columns)

		report_columns = {
			"hdmf_no": "Zip Code: ",
			"employee": zip_code,
			"last_name": "",
			"first_name": "",
			"middle_name": "Pag-IBIG ID: ",
			"HDMF": hdmf_id,
			"HDMFE": "",
			"tin": "",
			"birthdate": "",
		}
		data.append(report_columns)

		#report_columns = {
		#	"hdmf_no": "Employer Type: ",
		#	"employee": "",
		#	"last_name": "",
		#	"first_name": "",
		#	"middle_name": "Type of Payment: ",
		#	"HDMF": "",
		#	"HDMFE": "",
		#	"tin": "",
		#	"birthdate": "",
		#}
		#data.append(report_columns)

		report_columns = {
			"hdmf_no": "Pad-IBIG ID",
			"employee": "Employee ID",
			"last_name": "Last Name",
			"first_name": "First Name",
			"middle_name": "Middle Name",
			"HDMF": "Employee Contribution",
			"HDMFE": "Employer Contribution",
			"tin": "TIN",
			"birthdate": "Birth Date",
		}
		data.append(report_columns)

	for emp in employee_list:
		HDMF_amount = flt(HDMF_map.get(emp.name, {}).get("HDMF"))
		HDMF_amount += flt(HDMF_map.get(emp.name, {}).get("HDMFM"))
		HDMFE_amount = flt(HDMF_map.get(emp.name, {}).get("HDMFE"))
		row = {
			"hdmf_no": emp.hdmf_no,
			"employee": emp.employee,
			"last_name": emp.last_name,
			"first_name": emp.first_name,
			"middle_name": emp.middle_name,
			"HDMF": '{:,.2f}'.format(HDMF_amount),
			"HDMFE": '{:,.2f}'.format(HDMFE_amount),
			"tin": emp.tin,
			"birthdate": datetime.datetime.strftime(getdate(emp.birthday), "%Y%m%d"),
		}

		data.append(row)

	return data

def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = {
			"hdmf_no": d.get("hdmf_no"),
			"employee": d.get("employee"),
			"last_name": d.get("last_name"),
			"first_name": d.get("first_name"),
			"middle_name": d.get("middle_name"),
			"HDMF": d.get("HDMF"),
			"HDMFE": d.get("HDMFE"),
			"tin": d.get("tin"),
			"birthdate": d.get("birthdate"),
		}
		
		result.append(row)
	return result

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

def get_employees(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql(""" SELECT DISTINCT TE.`name`, TE.hdmf_no, PR.`employee`, UPPER(TE.last_name) as last_name, UPPER(TE.first_name) as first_name, UPPER(TE.middle_name) as middle_name, TE.`tin`, TE.`birthday`
			FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
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
		employees = frappe.db.sql(""" SELECT DISTINCT TE.`name`, TE.hdmf_no, PR.`employee`, UPPER(TE.last_name) as last_name, UPPER(TE.first_name) as first_name, UPPER(TE.middle_name) as middle_name, TE.`tin`, TE.`birthday`
			FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
			WHERE PR.company = %(company)s 
				AND PR.posting_date >= %(from_date)s
				AND PR.posting_date <= %(to_date)s
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`) 
			ORDER BY PR.employee_name """,{ 
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
