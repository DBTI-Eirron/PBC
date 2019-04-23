# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, getdate, cstr
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
	HDMF_types = ["HDMFM", "HDMF", "HDMFE"]
	if filters.include_header:
		data.append({'mid':'TOTAL EE/LOAN AMOUNT: '})
		data.append({'mid':'TOTAL ER AMOUNT: '})
		data.append({'mid':'RECORD COUNT: '})
		data.append({'mid':'MID','tin':'TIN','last_name':'Last Name','first_name':'First Name','middle_name':'Middle Name','birth_day':'Birth Date','ee':'EE / Loan Amount','er':'ER'})
	total_ee = 0.00
	total_er = 0.00
	total_count = 0
	for emp in employee_list:
		emp_cont = 0.00
		empr_cont = 0.00
		row = {'mid':emp.hdmf_no, 'tin':emp.tin, 'last_name':emp.last_name, 'first_name':emp.first_name, 'middle_name':emp.middle_name, 'birth_day':emp.birthday}
		result = []
		for d in HDMF_types:
			HDMF_amount = flt(register_map.get(emp.name, {}).get(d))
			result.append('{:,.2f}'.format(HDMF_amount))
		emp_cont = flt(result[0]) + flt(result[1])
		empr_cont = flt(result[2])
		row.update({'ee':'{:,.2f}'.format(emp_cont),'er':'{:,.2f}'.format(empr_cont)})
		total_ee += emp_cont
		total_er += empr_cont
		total_count += 1
		data.append(row)
	if filters.include_header:
		data[0]['first_name'] = total_ee
		data[1]['first_name'] = total_er
		data[2]['first_name'] = total_count
	return data

def get_employees(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee as `name`, TE.last_name, TE.first_name, TE.middle_name, TE.tin, TE.hdmf_no, TE.birthday FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
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
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee as `name`, TE.last_name, TE.first_name, TE.middle_name, TE.tin, TE.hdmf_no, TE.birthday  FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
				WHERE PR.company = %(company)s 
				AND PR.posting_date >= %(from_date)s
				AND PR.posting_date <= %(to_date)s
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`) ORDER BY PR.employee_name """,{ 
				"company": filters.company,
				"from_date": filters.from_date,
				"to_date": filters.to_date
			}, as_dict=True)

	return employees

def get_columns(filters):
	columns = [
		{
		"fieldname": "mid",
		"label": _("MID"),
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
		"fieldname": "ee",
		"label": _("EE / Loan Amount"),
		"fieldtype": "Data",
		"width": 100
		},{
		"fieldname": "er",
		"label": _("ER"),
		"fieldtype": "Data",
		"width": 100
		},
	]
	if filters.include_header:
		columns = [
			{
			"fieldname": "mid",
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
			"fieldname": "ee",
			"label": _(""),
			"fieldtype": "Data",
			"width": 100
			},{
			"fieldname": "er",
			"label": _(""),
			"fieldtype": "Data",
			"width": 100
			},
		]
	return columns

	
def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

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
