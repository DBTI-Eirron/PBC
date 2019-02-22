# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "remarks",
			"label": _("Remarks"),
			"fieldtype": "Data",
			"width": 250
		},
	]

	if filters.bank == "EastWest Bank":
		columns = [
			{
				"fieldname": "hdr",
				"label": _("HDR"),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "account_number",
				"label": _("Account Number"),
				"fieldtype": "Data",
				"width": 180
			},
			{
				"fieldname": "amount",
				"label": _("Amount"),
				"fieldtype": "Currency",
				"width": 120
			},
			{
				"fieldname": "remarks",
				"label": _("Remarks"),
				"fieldtype": "Data",
				"width": 250
			},
		]

	if filters.bank == "China Banking Corporation" or filters.bank == "Chinabank" or filters.bank == "China Bank" or filters.bank == "CBC":
		columns = [
			{
				"fieldname": "last_name",
				"label": _("Last Name"),
				"fieldtype": "Data",
				"width": 160
			},
			{
				"fieldname": "first_name",
				"label": _("First Name"),
				"fieldtype": "Data",
				"width": 160
			},
			{
				"fieldname": "account_number",
				"label": _("Account Number"),
				"fieldtype": "Data",
				"width": 160
			},{
				"fieldname": "account_type",
				"label": _("Account Type"),
				"fieldtype": "Data",
				"width": 140
			},
			{
				"fieldname": "amount",
				"label": _("Amount"),
				"fieldtype": "Currency",
				"width": 140
			},
		]

	if filters.bank == "Bank of the Philippine Islands" or filters.bank == "BPI" :
		columns = [
			{
				"fieldname": "detail",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "employee_name",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "employee_account",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "amount",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "remarks",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "lbl_total_amount",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "total_amount",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "lbl_total_count",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "total_count",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "lbl_funding_account",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "funding_account",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
		]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_net_pay(filters):
	if not "Administrator" in frappe.get_roles(frappe.session.user):
		document = frappe.db.sql(""" SELECT DISTINCT
			TE.last_name,
			TE.first_name,
			TE.middle_name,
			BT.employee,
			BT.employee_name,
			BT.employee_account,
			BT.bank_type,
			BT.amount,
			BT.remarks,
			BR.payroll_time,
			BR.payroll_schedule,
			BR.funding_account
			FROM
			`tabBank Remittance Setup` BR
			JOIN `tabBank Remittance Setup Table` BT ON BR.`name` = BT.parent 
			JOIN `tabEmployee` TE ON BT.employee = TE.`name`
			WHERE TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s)
			AND BR.payroll_period = %(period)s 
			AND BR.docstatus = 1 
			AND BR.company = %(company)s 
			AND BR.bank = %(bank)s 
			ORDER BY BT.employee_name ASC""",{
			"period": filters.payroll_period,
			"company": filters.company,
			"bank": filters.bank,
			"user": frappe.session.user
		}, as_dict=True)
	else:
		document = frappe.db.sql(""" SELECT DISTINCT
			TE.last_name,
			TE.first_name,
			TE.middle_name,
			BT.employee,
			BT.employee_name,
			BT.employee_account,
			BT.bank_type,
			BT.amount,
			BT.remarks,
			BR.payroll_time,
			BR.payroll_schedule,
			BR.funding_account
			FROM
			`tabBank Remittance Setup` BR
			JOIN `tabBank Remittance Setup Table` BT ON BR.`name` = BT.parent JOIN `tabEmployee` TE ON BT.employee = TE.`name`
			WHERE BR.payroll_period = %(period)s 
			AND BR.docstatus = 1 
			AND BR.company = %(company)s 
			AND BR.bank = %(bank)s 
			ORDER BY BT.employee_name ASC""",{
			"period": filters.payroll_period,
			"company": filters.company,
			"bank": filters.bank,
		}, as_dict=True)

	return document

def get_data(filters):
	data = []
	document = get_net_pay(filters)	

	for doc in document: 
		data.append(doc)

	return data
 
def get_result_as_list(data, filters):
	result = []
	total_count = 0
	total_amount = 0.00
	payroll_schedule = ""
	payroll_time = ""
	funding_account = ""

	for d in data:
		if d.amount < 1:
			d.amount = 0.00
		total_amount += flt(d.amount, 8)
		total_count += 1

		if d.payroll_time:
			payroll_schedule = d.payroll_schedule
			payroll_time = d.payroll_time

		funding_account = d.funding_account

	if filters.bank == "Bank of the Philippine Islands" or filters.bank == "BPI":
		if filters.include_header:
			payroll_date = frappe.db.get_value("Payroll Period", filters.payroll_period, "payroll_date")

			if payroll_time == "Pay Now":
				payroll_time = ""
			else:
				payroll_time = payroll_schedule 

			headers = {
				"detail": "H", 
				"employee_name": "Payroll Date",
				"employee_account": datetime.datetime.strftime(payroll_date, "%B %d, %Y"),
				"amount": "Payroll Time",
				"remarks": payroll_time,
				"lbl_total_amount": "Total Amount",
				"total_amount": '{:,.2f}'.format(total_amount),
				"lbl_total_count": "Total Count",
				"total_count": total_count, 
				"lbl_funding_account": "Funding Account", 
				"funding_account": funding_account
			}

			result.append(headers)

		fields = {
			"detail": "DETAIL CONSTANT",
			"employee_name": "EMPLOYEE NAME",
			"employee_account": "EMPLOYEE ACCOUNT",
			"amount": "AMOUNT",
			"remarks": "REMARKS",
		}

		result.append(fields)

		for d in data:
			row = {
				"detail": "D",
				"employee_name": d.get("employee_name"),
				"employee_account": d.get("employee_account"),
				"amount": '{:,.2f}'.format(d.get("amount")),
				"remarks": d.get("remarks"),
			}

			result.append(row)

		total = {
			"amount": '{:,.2f}'.format(total_amount),
			"employee": "TOTAL",
			"employee_name": total_count
		}

		result.append(total)

	elif filters.bank == "EastWest Bank":
		for d in data:
			row = {
				"hdr": "DTL",
				"account_number": d.get("employee_account"),
				"amount": '{:,.2f}'.format(d.get("amount")),
				"remarks": str(d.get("last_name"))+", "+str(d.get("first_name"))+", "+str(d.get("middle_name")),
			}
			result.append(row)

		total = {
			"hdr": "TLR",
			"account_number": total_count,
			"amount": '{:,.2f}'.format(total_amount),
			"remarks": "",
		}
		result.append(total)

	elif filters.bank == "China Banking Corporation" or filters.bank == "Chinabank" or filters.bank == "China Bank" or filters.bank == "CBC":
		for d in data:
			row = {
				"last_name" : d.get("last_name"),
				"first_name" : d.get("first_name"),
				"account_number" : d.get("employee_account"),
				"account_type" : d.get("bank_type"),
				"amount": '{:,.2f}'.format(d.get("amount")),
			}

			result.append(row)

		total = {
			"last_name" : "",
			"first_name" : "",
			"account_number" : "",
			"account_type" : "Total",
			"amount": '{:,.2f}'.format(total_amount),
		}

		result.append(total)

	else:
		for d in data:
			row = {
				"employee": d.get("employee"),
				"employee_name": d.get("employee_name"),
				"amount": '{:,.2f}'.format(d.get("amount")),
				"remarks": d.get("remarks"),
			}

			result.append(row)

		total = {
			"employee": "TOTAL",
			"employee_name": total_count,
			"amount": '{:,.2f}'.format(total_amount),
			"remarks": "",
		}

		result.append(total)

	return result