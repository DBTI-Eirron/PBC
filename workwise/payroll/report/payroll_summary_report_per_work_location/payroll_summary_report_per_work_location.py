# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "location",
			"label": _("Location"),
			"fieldtype": "Link",
			"options": "location",
			"width": 200
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "head_count",
			"label": _("Head Count"),
			"fieldtype": "Data",
			"width": 130
		},
	]
	return columns

def get_data(filters):
	data = []
	total_amount = total_head = 0
	location = get_location(filters)
	for loc in location:
		amount,head_count = get_values(loc.name,filters)
		data.append({'location':loc.name,'amount':format_precision(amount, filters.value_precision),'head_count':head_count})
		total_amount += amount
		total_head += head_count
	data.append({})
	data.append({'location':'Grand Total','amount':format_precision(total_amount, filters.value_precision),'head_count':total_head})
	data = add_by(data)
	return data


def get_values(location,filters):
	final_amount = final_head = 0
	amount = frappe.db.sql("""SELECT SUM(PR.net_payroll) as amount FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` E ON PR.employee = E.`name` WHERE E.location = %s AND PR.company = %s AND PR.posting_date BETWEEN %s AND %s"""+add_conditions(),(location,filters.company,filters.from_date,filters.to_date),as_dict=True)
	head_count = frappe.db.sql("""SELECT COUNT(PR.`name`) as head_count FROM `tabPayroll Register`PR INNER JOIN `tabEmployee` E ON PR.employee = E.`name` WHERE E.location = %s AND PR.company = %s AND PR.posting_date BETWEEN %s AND %s"""+add_conditions(),(location,filters.company,filters.from_date,filters.to_date),as_dict=True)
	if amount[0].amount:
		final_amount = amount[0].amount
	if head_count[0].head_count:
		final_head = head_count[0].head_count
	return final_amount, final_head

def add_conditions():
	condition = ""
	if frappe.session.user != "Administrator":
		condition += " AND E.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = '"+frappe.session.user+"' )"
	return condition

def get_location(filters):
	query = "SELECT TL.`name` FROM `tabLocation` TL WHERE TL.company = '"+filters.company+"'"
	if filters.location:
		query += " AND TL.`name` = '"+filters.location+"'"
	location = frappe.db.sql(query,as_dict=True)
	return location

def add_by(data):
	data.append({})
	data.append({'location':'Prepared By'})
	data.append({'location':'____________________________'})
	data.append({})
	data.append({'location':'Noted By'})
	data.append({'location':'____________________________'})
	data.append({})
	data.append({'location':'Processed By'})
	data.append({'location':'____________________________'})
	data.append({})
	data.append({'location':'Approved By'})
	data.append({'location':'____________________________'})
	return data