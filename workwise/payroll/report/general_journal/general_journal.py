# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

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
			"fieldname": "account_name",
			"label": _("Account"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "account_code",
			"label": _("Code"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Float",
			"width": 140
		},
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Float",
			"width": 140
		},		
	]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_accounts(filters):
	accounts = frappe.db.sql("""SELECT * FROM `tabAccount` 
		WHERE company = %(company)s ORDER BY account_code """,{
			"company": filters.company,
		}, as_dict=True)

	return accounts

def get_register(filters):
	register_list = frappe.db.sql("""SELECT * FROM `tabPayroll Register` 
		WHERE company = %(company)s AND posting_date >= %(from_date)s AND posting_date <= %(to_date)s""",{
			"company": filters.company,
			"from_date": filters.from_date,
			"to_date": filters.to_date,
		}, as_dict=True)
	
	return register_list

def get_data(filters):
	#Initialize
	data = []
	total_debit = 0
	total_credit = 0

	accounts = get_accounts(filters)
	register = get_register(filters)

	if accounts:
		for acc in accounts: 
			entry = {
				"account_name": acc.account_name,
				"account": acc.name,
				"account_code": acc.account_code,
				"balance": acc.default_balance,
				"debit": 0.0,
				"credit": 0.0,
			}

			for r in register:
				if r['account'] == entry['account']:
					if entry['balance'] == "Debit":
						entry['debit'] += r['amount']
					else:
						entry['credit'] += r['amount']

			total_debit += entry['debit']
			total_credit += entry['credit']
			data.append(entry)

		data.append({
				"account_name": _("TOTAL"),
				"debit": total_debit,
				"credit": total_credit,
			})

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = {
			"account_name": d.get("account_name"),
			"account_code": d.get("account_code"),
			"debit": d.get("debit"),
			"credit": d.get("credit"),
		}
		
		result.append(row)
	return result