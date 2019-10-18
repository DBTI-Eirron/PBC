# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	data = []
	employees = frappe.db.sql("""SELECT TE.`name`, TE.last_name, TE.first_name, TE.middle_name, TE.company, TE.position_title,TE.date_hired, TE.birthday, TE.age, TE.sss_no, TE.hdmf_no, TE.tin, TE.phic_no, TE.gender, TE.civil_status, TA.address_line1, TA.address_line2,TA.city, TA.county, TA.state, TA.country, 
(SELECT TC.mobile_no FROM `tabDynamic Link` DL INNER JOIN `tabContact` TC ON DL.parent = TC.`name` WHERE DL.parenttype = 'Contact' AND DL.link_name = TE.`name`) AS mobile_no,
(SELECT TC.phone FROM `tabDynamic Link` DL INNER JOIN `tabContact` TC ON DL.parent = TC.`name` WHERE DL.parenttype = 'Contact' AND DL.link_name = TE.`name`) AS phone  FROM `tabEmployee` TE
		LEFT JOIN `tabDynamic Link` DL ON TE.`name` = DL.link_name
		INNER JOIN `tabAddress` TA ON DL.parent = TA.`name`
	WHERE TE.company = %s AND DL.parenttype = 'Address'"""+add_filter(filters),(filters.company),as_dict=True);
	for emp in employees:
		contact = emp.mobile_no or emp.phone
		address = assemble_address(filters,emp)
		data.append({"employee":emp.name,"last_name":emp.last_name,"first_name":emp.first_name,"middle_name":emp.middle_name,"address":address,"contact":contact,"company":emp.company,"position_title":emp.position_title,"date_hired":emp.date_hired,"birthday":emp.birthday,"age":emp.age,"sss_no":emp.sss_no,"hdmf_no":emp.hdmf_no,"tin":emp.tin,"phic_no":emp.phic_no,"gender":emp.gender,"civil_status":emp.civil_status})
	return data

def add_filter(filters):
	conditions = ""
	if filters.employee:
		conditions += "AND TE.`name` ='"+filters.employee+"'"
	return conditions

def assemble_address(filters,emp):
	address = cstr(emp.address_line1)
	if emp.address_line2:
		address += ", " +cstr(emp.address_line2)
	address += ", "+cstr(emp.city)
	if emp.county:
		address += ", " +cstr(emp.county)
	if emp.state:
		address += ", " +cstr(emp.state)
	address += ", "+cstr(emp.country)

	return address

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options":"Employee",
			"width": 150
		},
		{
			"fieldname": "last_name",
			"label": _("Last Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "first_name",
			"label": _("First Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "middle_name",
			"label": _("Middle Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "address",
			"label": _("Address"),
			"fieldtype": "Data",
			"width": 300
		},
		{
			"fieldname": "contact",
			"label": _("Contact"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "company",
			"label": _("Company"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "position_title",
			"label": _("Position Title"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "date_hired",
			"label": _("Date Hired"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "birthday",
			"label": _("Birthday"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "age",
			"label": _("Age"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "sss_no",
			"label": _("SSS Number"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "hdmf_no",
			"label": _("HDMF Number"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "tin",
			"label": _("TIN Number"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "phic_no",
			"label": _("PHIC Number"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "gender",
			"label": _("Gender"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "civil_status",
			"label": _("Civil Status"),
			"fieldtype": "Data",
			"width": 150
		},
	]
	return columns