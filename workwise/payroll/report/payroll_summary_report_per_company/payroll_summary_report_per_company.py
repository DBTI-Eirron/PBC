# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "company",
			"label": _("Company"),
			"fieldtype": "Link",
			"options": "Company",
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
	company = get_company(filters)
	for comp in company:
		amount,head_count = get_values(comp.company_name,filters.from_date,filters.to_date)
		data.append({'company':comp.company_name,'amount':'{:20,.2f}'.format(flt(amount)),'head_count':head_count})
		total_amount += amount
		total_head += head_count
	data.append({})
	data.append({'company':'Grand Total','amount':'{:20,.2f}'.format(flt(total_amount)),'head_count':total_head})
	data = add_by(data)
	return data


def get_values(company,from_date,to_date):
	final_amount = final_head = 0
	amount = frappe.db.sql("""SELECT SUM(PR.net_payroll) as amount FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` E ON PR.employee = E.name WHERE PR.company = %s AND PR.posting_date BETWEEN %s AND %s"""+add_conditions(),(company,from_date,to_date),as_dict=True)
	head_count = frappe.db.sql("""SELECT COUNT(PR.`name`) as head_count FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` E ON PR.employee = E.name WHERE PR.company = %s AND PR.posting_date BETWEEN %s AND %s"""+add_conditions(),(company,from_date,to_date),as_dict=True)
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

def get_company(filters):
	query = "SELECT `company_name` FROM `tabCompany`"
	if filters.company:
		query += " WHERE company_name = '"+filters.company+"'"
	company = frappe.db.sql(query,as_dict=True)
	return company

def add_by(data):
	data.append({})
	data.append({'company':'Prepared By'})
	data.append({'company':'____________________________'})
	data.append({})
	data.append({'company':'Approved By'})
	data.append({'company':'____________________________'})
	data.append({})
	data.append({'company':'Noted By'})
	data.append({'company':'____________________________'})
	return data