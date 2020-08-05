# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_decimal_by_2, format_decimal_by_2_align_right, format_decimal_by_2_align_right_negative
from frappe import _

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "posting_date",
			"label": _("Posting Date"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "document_no",
			"label": _("Document No."),
			"fieldtype": "Integer",
			"width": 140
		},
		{
			"fieldname": "account_type",
			"label": _("Account Type"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "account_number",
			"label": _("G/L Account No."),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "description",
			"label": _("Description"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "account_name",
			"label": _("Account"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "cost_center",
			"label": _("Cost Center"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "parent_cost_center",
			"label": _("Parent Cost Center"),
			"fieldtype": "Data",
			"width": 140
		},		
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Data",
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
		WHERE company = %(company)s ORDER BY account_number """,{
			"company": filters.company,
		}, as_dict=True)

	return accounts

def get_cost_center(filters):
	conditions = ""
	if filters.cost_center:
		conditions = "WHERE `name` = %(cost_center)s"

	accounts = frappe.db.sql("""SELECT * FROM `tabCost Center` {conditions} ORDER BY cost_center_code """.format(conditions=conditions),{
		"company": filters.company,
		"cost_center": filters.cost_center,
	}, as_dict=True)

	return accounts

def get_account_setting_map(filters):
	acct_map = {}
	acct_settings = frappe.db.sql("""SELECT TT.`code`, TTA.debit_account, TTA.debit_code, TTA.credit_account, TTA.credit_code
		FROM `tabTransaction Type` TT  INNER JOIN `tabTransaction Type Accounts` TTA ON TT.`name` = TTA.parent AND TTA.`company` = %(company)s """,{
		"company": filters.company,
	}, as_dict=True)

	for d in acct_settings:
		acct_map[d.code] = {
			"pay_code": d.code,
			"debit_account": d.debit_account, 
			"credit_account": d.credit_account,
			"debit_code": d.debit_code, 
			"credit_code": d.credit_code,
		}

	return acct_map

def get_account_wise_registers(filters):
	account_wise_registers = []
	acct_map = get_account_setting_map(filters)

	registers = frappe.db.sql("""SELECT PR.posting_date, PE.pay_code, PE.amount, PE.cost_center FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PE ON PE.parent = PR.`name`
		INNER JOIN `tabPayroll Period` PP ON PP.name = PR.period
		INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		WHERE PR.company = %(company)s 
		AND PR.posting_date >= %(from_date)s 
		AND PR.posting_date <= %(to_date)s 
		AND PR.on_hold != 1 
		AND PE.entry_type = "Employer"
		{conditions} """.format( conditions=get_conditions(filters) ), {
			"company": filters.company,
			"from_date": filters.from_date,
			"to_date": filters.to_date,
			"cost_center": filters.cost_center,
		}, as_dict=True)
	
	for d in registers:
		entry = {
			"posting_date": d.posting_date,
			"pay_code": d.pay_code,
			"cost_center": d.cost_center,
			"amount": d.amount,
			"debit_account": None, 
			"credit_account": None,
			"debit_code": None, 
			"credit_code": None,
		}

		if d.pay_code in acct_map: #Update Account per Entry
			if acct_map[d.pay_code]['debit_account']:
				entry['debit_account'] = acct_map[d.pay_code]['debit_account']

			if acct_map[d.pay_code]['debit_code']:
				entry['debit_code'] = acct_map[d.pay_code]['debit_code']

			if acct_map[d.pay_code]['credit_account']:
				entry['credit_account'] = acct_map[d.pay_code]['credit_account']

			if acct_map[d.pay_code]['credit_code']:
				entry['credit_code'] = acct_map[d.pay_code]['credit_code']

			account_wise_registers.append(entry)

	return account_wise_registers

def get_conditions(filters):
	conditions = []
	if filters.cost_center:
		conditions.append("PE.cost_center=%(cost_center)s")

	if frappe.session.user != "Administrator":
		conditions.append(_("PR.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_data(filters):
	#Initialize
	data = []
	total_debit = 0
	total_credit = 0
	total_amount = 0
	accounts = get_accounts(filters)
	cost_center = get_cost_center(filters)
	registers = get_account_wise_registers(filters)

	from_str = datetime.datetime.strftime(getdate(filters.from_date),'%b %d, %Y')
	to_str = datetime.datetime.strftime(getdate(filters.to_date),'%b %d, %Y')

	if accounts and registers:
		for acc in accounts: 
			for cost in cost_center: 
				entry = {
					"posting_date": "",
					"document_no": 1,
					"account_type": "G/L Account",
					"description": ""+from_str+" - "+to_str+"",
					"account_name": acc.account_name,
					"account": acc.name,
					"account_number": acc.name,
					"balance": acc.default_balance,
					"parent_cost_center": cost.parent_cost_center,
					"cost_center": cost.name,
					"debit": 0.0,
					"credit": 0.0,
				}

				for r in registers:
					entry['posting_date'] = r.get('posting_date')
					if r.get('debit_account') == entry['account_number'] and r.get('cost_center') == entry['cost_center']:
						entry['debit'] += r['amount']

					if r.get('credit_account') == entry['account_number'] and r.get('cost_center') == entry['cost_center']:
						entry['credit'] += r['amount']

				amount = entry['debit'] - entry['credit']
				entry['amount'] = format_decimal_by_2_align_right(amount)
				if amount < 0:
					entry['amount'] = format_decimal_by_2_align_right_negative(amount)

				total_debit += entry['debit']
				total_credit += entry['credit']
				
				if entry['debit'] > 1 or entry['credit'] > 1:
					data.append(entry)

		data.append({
			"account_name": _("TOTAL"),
			"debit": format_decimal_by_2_align_right(total_debit),
			"credit": format_decimal_by_2_align_right(total_credit),
		})

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:	
		result.append(d)

	return result