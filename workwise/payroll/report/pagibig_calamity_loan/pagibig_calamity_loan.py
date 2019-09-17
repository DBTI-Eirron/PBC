# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_decimal_by_2
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	validate_filters(filters)

	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	data = []
	entries = []
	transaction_type = ["HDMFCL"]
	gov_map = get_employees(filters,transaction_type)
	if not gov_map:
		frappe.msgprint("No Records Found");

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
	for emp in gov_map:
		row = {
			'pib':gov_map[emp]['hdmf_no'], 
			'tin':gov_map[emp]['tin'], 
			'last_name':gov_map[emp]['last_name'], 
			'first_name':gov_map[emp]['first_name'], 
			'middle_name':gov_map[emp]['middle_name'], 
			'birth_day':gov_map[emp]['birthday'],
			'map':format_decimal_by_2(gov_map[emp]['HDMFCL'])
		}
		total_map += gov_map[emp]['HDMFCL']
		entries.append(row)
		entries = sorted(entries, key = lambda k:k['last_name'])
	for ent in entries:
		data.append(ent)
	data.append({'birth_day':'Total :'+str(format_decimal_by_2(total_map))})
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

