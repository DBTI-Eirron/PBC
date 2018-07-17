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
			"fieldname": "account_number",
			"label": _("Account Number"),
			"fieldtype": "Data",
			"options": "Employee.bank_primary",
			"width": 140
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Float",
			"width": 140
		},
		{
			"fieldname": "remarks",
			"label": _("Remarks"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 250
		},	
	]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_net_pay(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		loans = frappe.db.sql("""SELECT
					tr.employee AS employee,
					te.bank_primary AS bank_primary,
					tr.net_payroll AS net_payroll,
					te.full_name AS full_name 
				FROM
					`tabPayroll Register` AS tr
					INNER JOIN `tabEmployee` AS te ON tr.employee = te.NAME 
				WHERE
					tr.period = %(payroll_period)s 
					AND tr.company = %(company)s 
					AND te.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
							INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`
							WHERE SU.allow_user = %(user)s)
				ORDER BY
					te.full_name ASC""",{
				"payroll_period": filters.payroll_period,
				"company": filters.company,
				"user": cur_user
			}, as_dict=True)
	else:
		loans = frappe.db.sql("""SELECT
					tr.employee AS employee,
					te.bank_primary AS bank_primary,
					tr.net_payroll AS net_payroll,
					te.full_name AS full_name 
				FROM
					`tabPayroll Register` AS tr
					INNER JOIN `tabEmployee` AS te ON tr.employee = te.NAME 
				WHERE
					tr.period = %(payroll_period)s 
					AND tr.company = %(company)s 
					AND te.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
							INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
				ORDER BY
					te.full_name ASC""",{
				"payroll_period": filters.payroll_period,
				"company": filters.company,
				"user": cur_user
			}, as_dict=True)

	return loans

def get_data(filters):
	data = []
	loans = get_net_pay(filters)

	for loan in loans: 
		data.append(loan)

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = {
			"account_number": d.get("bank_primary"),
			"amount": d.get("net_payroll"),
			"remarks": d.get("full_name")
		}
		
		result.append(row)
	return result