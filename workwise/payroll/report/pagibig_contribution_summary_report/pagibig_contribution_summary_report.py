# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	validate_filters(filters)

	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

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

def get_data(filters):
	#Initialize
	data = []
	transaction_type = ['HDMF','HDMFE']

	gov_map = get_employees(filters,transaction_type)
	if not gov_map:
		frappe.msgprint("No Records Found");
	else:
		if filters.include_header:
			company = frappe.db.sql("""SELECT TC.hdmf_id,TC.phone, TA.address_title, TA.city, TA.pincode
				FROM `tabCompany` TC
				LEFT JOIN `tabDynamic Link` DL ON TC.`name` = DL.link_name
				LEFT JOIN `tabAddress` TA ON DL.parent = TA.`name`
				LIMIT 1
				""", as_dict=1)

			address = ""
			zip_code = ""
			contact = ""
			hdmf_id = ""
			if company:
				if company[0]['address_title'] or company[0]['city']:
					address = str(company[0]['address_title'])+", "+str(company[0]['city'])
				if company[0]['pincode']:
					zipcode = str(company[0]['pincode'])
				if company[0]['phone']:
					contact = str(company[0]['phone'])
				if company[0]['hdmf_id']:
					hdmf_id = str(company[0]['hdmf_id'])

			headers = [{
				"hdmf_no": "Employer's Name: ",
				"employee": filters.company,
				"last_name": "",
				"first_name": "",
				"middle_name": "Contact Number: ",
				"HDMF": contact,
				"HDMFE": "",
				"tin": "",
				"birthdate": "",
			},{
				"hdmf_no": "Address: ",
				"employee": address,
				"last_name": "",
				"first_name": "",
				"middle_name": "",
				"HDMF": "",
				"HDMFE": "",
				"tin": "",
				"birthdate": "",
			},{
				"hdmf_no": "Zip Code: ",
				"employee": zip_code,
				"last_name": "",
				"first_name": "",
				"middle_name": "Pag-IBIG ID: ",
				"HDMF": hdmf_id,
				"HDMFE": "",
				"tin": "",
				"birthdate": "",
			},{
				"hdmf_no": "Pad-IBIG ID",
				"employee": "Employee ID",
				"last_name": "Last Name",
				"first_name": "First Name",
				"middle_name": "Middle Name",
				"HDMF": "Employee Contribution",
				"HDMFE": "Employer Contribution",
				"tin": "TIN",
				"birthdate": "Birth Date",
			}]
			data += headers

		total_hdmfe, total_hdmf = 0, 0
		for emp in sorted(gov_map.items(), key = lambda k:k[1]['full_name']):
			total_hdmfe += gov_map[emp[0]]['HDMFE']
			total_hdmf += gov_map[emp[0]]['HDMF']
			row = {
				"hdmf_no": gov_map[emp[0]]['hdmf_no'],
				"employee": emp[0],
				"last_name": gov_map[emp[0]]['last_name'],
				"first_name": gov_map[emp[0]]['first_name'],
				"middle_name": gov_map[emp[0]]['middle_name'],
				"HDMF": format_precision(gov_map[emp[0]]['HDMF'], filters.value_precision),
				"HDMFE": format_precision(gov_map[emp[0]]['HDMFE'], filters.value_precision),
				"tin": gov_map[emp[0]]['tin'],
				"birthdate": datetime.datetime.strftime(getdate(gov_map[emp[0]]['birthday']), "%Y%m%d"),
			}
			data.append(row)
		#Totals
		data.append({
			"hdmf_no": "",
			"employee": "",
			"last_name": "",
			"first_name": "",
			"middle_name": "",
			"HDMF": total_hdmfe,
			"HDMFE": total_hdmf,
			"tin": "",
			"birthdate": "",
		})

	return data


def get_employees(filters,transaction_type):
	employees = frappe.db.sql("""SELECT PRE.pay_code, PRE.amount, PR.posting_date, PR.employee as `name`, PR.employee_name as full_name, TE.hdmf_no, TE.first_name, TE.last_name, TE.middle_name, TE.tin, TE.birthday
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

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))