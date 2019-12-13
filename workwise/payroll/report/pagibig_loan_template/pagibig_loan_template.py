# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _, msgprint

def execute(filters=None):
	validate_filters(filters)
	data =  get_data(filters)
	columns = get_columns(filters)
	return columns, data

def get_data(filters):
	data = []
	employee_list = get_employees(filters)
	register_map = get_HDMF_map(filters, employee_list)
	HDMF_types = ["HDMFL"]
	if filters.include_header:
		address = frappe.db.sql("""SELECT A.`pincode`, A.address_line1, A.city FROM `tabDynamic Link` DL INNER JOIN `tabAddress` A ON DL.parent = A.name WHERE DL.link_name = %s""",(filters.company),as_dict=True)
		final_address = ""
		zipcode = ""
		if address:
			if address[0].pincode:
				zipcode = address[0].pincode
			if address[0].address_line1:
				final_address += address[0].address_line1
			if address[0].city:
				final_address += address[0].city
		contact_number,hdmf_id = frappe.get_value('Company',filters.company,['phone','hdmf_id'])
		data.append({'pib':"Employer's Name: ",'tin':filters.company,'middle_name':'Contact Number: ','birth_day':contact_number})
		data.append({'pib':'Address: ','tin':final_address})
		data.append({'pib':'ZIP Code: ','tin':zipcode,'middle_name':'Pag-Ibig No.: ','birth_day':hdmf_id})
		data.append({})
		data.append({'pib':'Pag-Ibig ID','tin':'TIN','last_name':'Last Name','first_name':'First Name','middle_name':'Middle Name','birth_day':'Birth Date','map':'Monthly Amortization Payment'})
	total_map = 0.00
	for emp in employee_list:
		emp_map = 0.00
		result = []
		for d in HDMF_types:
			HDMF_amount = flt(register_map.get(emp.name, {}).get(d))
			result.append(format_precision(HDMF_amount, filters.value_precision))
		emp_map = flt(result[0])
		if emp_map > 0:
			row = {'pib':emp.hdmf_no, 'tin':emp.tin, 'last_name':emp.last_name, 'first_name':emp.first_name, 'middle_name':emp.middle_name, 'birth_day':(emp.birthday).strftime('%m/%d/%Y')}
			row.update({'map':format_precision(emp_map, filters.value_precision)})
			total_map += emp_map
			data.append(row)
	return data

def get_employees(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee as `name`, TE.last_name, TE.first_name, TE.middle_name, TE.tin, TE.hdmf_no, TE.birthday FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
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
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee as `name`, TE.last_name, TE.first_name, TE.middle_name, TE.tin, TE.hdmf_no, TE.birthday  FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
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

def get_columns(filters):
	columns = [
		{
		"fieldname": "pib",
		"label": _("Pag-Ibig ID"),
		"fieldtype": "Data",
		"width": 170
		},{
		"fieldname": "tin",
		"label": _("TIN"),
		"fieldtype": "Data",
		"width": 100
		},{
		"fieldname": "last_name",
		"label": _("Last Name"),
		"fieldtype": "Data",
		"width": 120
		},{
		"fieldname": "first_name",
		"label": _("First Name"),
		"fieldtype": "Data",
		"width": 120
		},{
		"fieldname": "middle_name",
		"label": _("Middle Name"),
		"fieldtype": "Data",
		"width": 120
		},{
		"fieldname": "birth_day",
		"label": _("Birth Date"),
		"fieldtype": "Data",
		"width": 100
		},{
		"fieldname": "map",
		"label": _("Monthly Amortization Payment"),
		"fieldtype": "Data",
		"width": 200
		}
	]
	if filters.include_header:
		columns = [
			{
			"fieldname": "pib",
			"label": _(""),
			"fieldtype": "Data",
			"width": 170
			},{
			"fieldname": "tin",
			"label": _(""),
			"fieldtype": "Data",
			"width": 100
			},{
			"fieldname": "last_name",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
			},{
			"fieldname": "first_name",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
			},{
			"fieldname": "middle_name",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
			},{
			"fieldname": "birth_day",
			"label": _(""),
			"fieldtype": "Data",
			"width": 100
			},{
			"fieldname": "map",
			"label": _(""),
			"fieldtype": "Data",
			"width": 200
			}
		]
	return columns

	
def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

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
