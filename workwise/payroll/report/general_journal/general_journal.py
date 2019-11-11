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
			"fieldname": "account_code",
			"label": _("Account Code"),
			"fieldtype": "Data",
			"width": 260
		},
		{
			"fieldname": "account_name",
			"label": _("Account"),
			"fieldtype": "Data",
			"width": 340
		},
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Currency",
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
		WHERE company = %(company)s """,{
			"company": filters.company,
		}, as_dict=True)

	return accounts

def get_register(filters):
	register_list = frappe.db.sql("""SELECT PE.pay_code, PE.amount FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PE ON PE.parent = PR.`name`
		INNER JOIN `tabTransaction Type` TT ON TT.code = PE.pay_code
		WHERE PR.company = %(company)s AND PR.posting_date >= %(from_date)s AND PR.posting_date <= %(to_date)s""",{
			"company": filters.company,
			"from_date": filters.from_date,
			"to_date": filters.to_date
		}, as_dict=True)

	return register_list

def get_transaction_map():
	tr_map = {}
	tr = frappe.db.sql("""SELECT code, title, type, entry_type, account, is_taxable, is_bonus, 
		is_government, is_standard, is_active FROM `tabTransaction Type` """, as_dict=1)

	for t in tr:
		tr_map[t.code] = {"code": t.code, "title": t.title, "type": t.type, "entry_type": t.entry_type,	"account": t.account, 
			"is_taxable": t.is_taxable, "is_standard": t.is_standard, "is_active": t.is_active, "is_bonus": t.is_bonus, "is_government": t.is_government,
		}

	return tr_map

def get_transaction_accts_map(filters):
	ta_map = {}
	ta = frappe.db.sql("""SELECT TT.code, TTA.company, TTA.debit_account, TTA.credit_account FROM `tabTransaction Type` TT
		INNER JOIN `tabTransaction Type Accounts` TTA ON TTA.parent = TT.`name` WHERE TTA.company = %s """, filters.company, as_dict=1)

	for d in ta:
		ta_map[d.code] = {"code": d.code, "company": d.company, 
			"debit_account": d.debit_account, "credit_account": d.credit_account,
		}

	return ta_map

def get_data(filters):
	#Initialize
	data = []
	total_debit = 0
	total_credit = 0

	accounts = get_accounts(filters)
	register = get_register(filters)
	tr_map = get_transaction_map()
	ta_map = get_transaction_accts_map(filters)

	if accounts and register:
		data.append({ "account_code": filters.company })
		data.append({ "account_code": datetime.datetime.strptime(str(getdate(filters.from_date)), '%Y-%m-%d').strftime('%B %d, %Y') 
			+" to "+ datetime.datetime.strptime(str(getdate(filters.to_date)), '%Y-%m-%d').strftime('%B %d, %Y') })

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
				if r.get('pay_code') in ta_map:
					if ta_map[r.get('pay_code')]['debit_account'] == entry['account']:
						entry['debit'] += r['amount']

					if ta_map[r.get('pay_code')]['credit_account']  == entry['account']:
						entry['credit'] += r['amount']			

			total_debit += entry['debit']
			total_credit += entry['credit']
			
			if entry['debit'] > 1 or entry['credit'] > 1:
				data.append(entry)

		data.append({
				"account_name": _("TOTAL"),
				"debit": '{:,.2f}'.format(total_debit),
				"credit": '{:,.2f}'.format(total_credit),
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