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
			"fieldtype": "Float",
			"width": 120
		},
	]

	if filters.bank == "Bank of the Philippine Islands" or filters.bank == "BPI" :
		columns += [
			{
				"fieldname": "payroll_schedule",
				"label": _("Payroll Time"),
				"fieldtype": "Time",
				"width": 120
			},
		]

	columns += [	
		{
			"fieldname": "remarks",
			"label": _("Remarks"),
			"fieldtype": "Data",
			"width": 250
		},
	]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_net_pay(filters):
	document = frappe.db.sql(""" SELECT
		BT.employee,
		BT.employee_name,
		BT.amount,
		BT.remarks,
		BR.payroll_schedule
		FROM
		`tabBank Remittance Setup` BR
		JOIN `tabBank Remittance Setup Table` BT 
		WHERE
		BR.`name` = BT.parent AND BR.payroll_period = %(period)s AND BR.docstatus = 1 AND BR.company = %(company)s AND BR.bank = %(bank)s """,{
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
	for d in data:
		row = {
			"employee": d.get("employee"),
			"employee_name": d.get("employee_name"),
			"amount": d.get("amount"),
			"remarks": d.get("remarks"),
			"payroll_schedule": d.get("payroll_schedule")
		}
		
		total_amount += d.amount
		total_count += 1

		result.append(row)

	total = {
		"amount": total_amount,
		"employee": "<b>TOTAL</b>",
		"employee_name": total_count
	}

	result.append(total)

	return result