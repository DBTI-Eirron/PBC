# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_decimal_by_2, format_decimal_by_2_align_right, format_decimal_by_2_align_right_negative
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	validate_filters(filters)

	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data
def get_data(filters):
	data = []
	transaction_type = ["HDMFM", "HDMF", "HDMFE"]
	gov_map = get_employees(filters,transaction_type)
	if not gov_map:
		frappe.msgprint("No Records Found");

	if filters.include_header:
		data.append({'mid':'TOTAL EE/LOAN AMOUNT: '})
		data.append({'mid':'TOTAL ER AMOUNT: '})
		data.append({'mid':'RECORD COUNT: '})
		data.append({'mid':'MID','tin':'TIN','last_name':'Last Name','first_name':'First Name','middle_name':'Middle Name','birth_day':'Birth Date','ee':'EE / Loan Amount','er':'ER'})

	total_ee = 0.00
	total_er = 0.00
	total_count = 0
	for emp in sorted(gov_map.items(), key = lambda k:k[1]['full_name']):
		employee = flt(gov_map[emp[0]]['HDMFM'])+flt(gov_map[emp[0]]['HDMF'])
		employer = gov_map[emp[0]]['HDMFE']
		row = {
			'mid':gov_map[emp[0]]['hdmf_no'], 
			'tin':gov_map[emp[0]]['tin'], 
			'last_name':gov_map[emp[0]]['last_name'], 
			'first_name':gov_map[emp[0]]['first_name'], 
			'middle_name':gov_map[emp[0]]['middle_name'], 
			'birth_day': datetime.datetime.strftime(getdate(gov_map[emp[0]]['birthday']), "%Y%m%d"),
			'ee':format_decimal_by_2(employee),
			'er':format_decimal_by_2(employer)
		}
		data.append(row)
		total_ee += employee
		total_er += employer
		total_count += 1
	if filters.include_header:
		data[0]['first_name'] = total_ee
		data[1]['first_name'] = total_er
		data[2]['first_name'] = total_count
	return data

def get_employees(filters,transaction_type):
	employees = frappe.db.sql("""SELECT PRE.pay_code, PRE.amount, PR.posting_date, PR.employee as `name`, PR.employee_name as full_name, TE.hdmf_no, TE.tin, TE.first_name, TE.last_name, TE.middle_name, TE.tin, TE.birthday
		FROM `tabPayroll Register Entries` PRE
		INNER JOIN `tabPayroll Register` PR ON PRE.`parent` = PR.`name`
		INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		WHERE PRE.pay_code IN ('"""+"','".join(str(e) for e in transaction_type)+"""') 
		AND PR.company = %(company)s 
		AND PR.posting_date BETWEEN %(from_date)s AND %(to_date)s
		AND TE.is_active = 1
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
			type_list.update({"full_name":d.full_name,"hdmf_no":d.hdmf_no,"employee":d.name,"first_name":d.first_name,"last_name":d.last_name,"middle_name":d.middle_name,"tin":d.tin,"birthday":d.birthday})
			gov_map.setdefault(d.name, frappe._dict(type_list))
		gov_map[d.name][d.pay_code] += flt(d.amount)
	return gov_map

def get_conditions(filters):
	conditions = []
	if frappe.session.user != "Administrator":
		conditions.append(_("TE.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

	if filters.period_group:
		conditions.append(_("TE.`period_group` = '{0}'").format(filters.period_group))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

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

