# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _
import math

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
		},{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Data",
			"width": 130
		},{
			"fieldname": "head_count",
			"label": _("No. of Employee"),
			"fieldtype": "Data",
			"width": 130
		},{
			"fieldname": "percent",
			"label": _(""),
			"fieldtype": "Data",
			"width": 70
		},{
			"fieldname": "per_ermployee",
			"label": _("Per Employee"),
			"fieldtype": "Data",
			"width": 150
		}
	]
	return columns

def get_data(filters):
	data = []
	company_dict = frappe.db.sql("""SELECT `name` FROM `tabCompany`""",as_dict=True)
	on_hold_list, cash_list, bank_list = get_payroll_reg(filters,company_dict)
	on_hold_total, cash_total, bank_total, grand_total, on_hold_perc, cash_perc, bank_perc, on_hold_heads, cash_heads, bank_heads, total_heads = get_percentage(on_hold_list, cash_list, bank_list)

	if not filters.mode_of_payment or filters.mode_of_payment == "BANK":
		data.append({'company': 'BANK'})
		for company in company_dict:
			c_total = 0
			count = 0
			for bank in bank_list:
				if bank.company == company.name:
					c_total += bank.amount
					count += 1
			if count > 0:
				per = c_total / count
			else:
				per = 0
			data.append({'company':company.name,'amount':'{:,.2f}'.format(c_total),'head_count':count,'percent':' ','per_ermployee':'{:,.2f}'.format(per)})
		if bank_heads:
			tper = bank_total / bank_heads
		else:
			tper = 0
		data.append({'company':'Total','amount':'{:,.2f}'.format(bank_total),'head_count':bank_heads,'percent':bank_perc,'per_ermployee':'{:,.2f}'.format(tper)})
		data.append({})

	if not filters.mode_of_payment or filters.mode_of_payment == "CASH":
		data.append({'company': 'CASH'})
		for company in company_dict:
			c_total = 0
			count = 0
			for cash in cash_list:
				if cash.company == company.name:
					c_total += cash.amount
					count += 1
			if count > 0:
				per = c_total / count
			else:
				per = 0
			data.append({'company':company.name,'amount':'{:,.2f}'.format(c_total),'head_count':count,'percent':' ','per_ermployee':'{:,.2f}'.format(per)})
		if cash_heads:
			tper = cash_total / cash_heads
		else:
			tper = 0
		data.append({'company':'Total','amount':'{:,.2f}'.format(cash_total),'head_count':cash_heads,'percent':cash_perc,'per_ermployee':'{:,.2f}'.format(tper)})
		data.append({})

	if not filters.mode_of_payment or filters.mode_of_payment == "ON HOLD":
		data.append({'company': 'ON HOLD'})
		for company in company_dict:
			c_total = 0
			count = 0
			for on_hold in on_hold_list:
				if on_hold.company == company.name:
					c_total += on_hold.amount
					count += 1
			if count > 0:
				per = c_total / count
			else:
				per = 0
			data.append({'company':company.name,'amount':'{:,.2f}'.format(c_total),'head_count':count,'percent':' ','per_ermployee':'{:,.2f}'.format(per)})
		if on_hold_heads:
			tper = on_hold_total / on_hold_heads
		else:
			tper = 0
		data.append({'company':'Total','amount':'{:,.2f}'.format(on_hold_total),'head_count':on_hold_heads,'percent':on_hold_perc,'per_ermployee':'{:,.2f}'.format(tper)})
		data.append({})

	if total_heads:
		if filters.mode_of_payment == "BANK":
			total_percent = bank_perc
		elif filters.mode_of_payment == "CASH":
			total_percent = cash_perc
		elif filters.mode_of_payment == "ON HOLD":
			total_percent = on_hold_perc
		else:
			total_percent = "100.00%"
	else:
		total_percent = "0.00%"
	if filters.mode_of_payment == "BANK":
		data.append({'company':'Grand Total','amount':'{:,.2f}'.format(bank_total),'head_count':bank_heads,'percent':total_percent,'per_ermployee':'{:,.2f}'.format(bank_total/bank_heads)})
	elif filters.mode_of_payment == "CASH":
		data.append({'company':'Grand Total','amount':'{:,.2f}'.format(cash_total),'head_count':cash_heads,'percent':total_percent,'per_ermployee':'{:,.2f}'.format(cash_total/cash_heads)})
	elif filters.mode_of_payment == "ON HOLD":
		data.append({'company':'Grand Total','amount':'{:,.2f}'.format(on_hold_total),'head_count':on_hold_heads,'percent':total_percent,'per_ermployee':'{:,.2f}'.format(on_hold_total/on_hold_heads)})
	else:
		data.append({'company':'Grand Total','amount':'{:,.2f}'.format(grand_total),'head_count':total_heads,'percent':total_percent,'per_ermployee':'{:,.2f}'.format(bank_total/bank_heads)})
	data = add_by(data)
	return data

def get_payroll_reg(filters,company_dict):
	add_filter = ""
	if filters.position_title:
		add_filter += "AND E.position_title = '"+filters.position_title+"'"
	if frappe.session.user != "Administrator":
		add_filter += " AND E.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = '"+frappe.session.user+"' )"
	pay_reg = frappe.db.sql("""SELECT PR.net_payroll AS amount, PR.company,PR.on_hold,E.mode_of_payment FROM `tabPayroll Register`PR INNER JOIN `tabEmployee` E ON PR.employee = E.name WHERE E.mode_of_payment <>'' AND E.mode_of_payment <> 'cheque' AND PR.posting_date BETWEEN %s AND %s"""+add_filter,(filters.from_date,filters.to_date),as_dict=True)
	on_hold_list = []
	cash_list = []
	bank_list = []
	for reg in pay_reg:
		if reg.on_hold == 1:
			on_hold_list.append(reg)
		else:
			if reg.mode_of_payment == "Cash":
				cash_list.append(reg)
			elif reg.mode_of_payment == "Bank":
				bank_list.append(reg)
	return on_hold_list, cash_list, bank_list

def get_percentage(on_hold_list, cash_list, bank_list):
	on_hold_total = cash_total = bank_total = total_heads = grand_total = 0.00
	on_hold_heads = cash_heads = bank_heads = 0
	for on_hold in on_hold_list:
		on_hold_total += on_hold.amount
		grand_total += on_hold.amount
		on_hold_heads += 1
		total_heads+= 1
	for cash in cash_list:
		cash_total += cash.amount
		grand_total += cash.amount
		cash_heads += 1
		total_heads +=1
	for bank in bank_list:
		bank_total += bank.amount
		grand_total += bank.amount
		bank_heads += 1
		total_heads += 1

	if on_hold_total > 0:
		on_hold_perc = str(flt(round((on_hold_total / grand_total) * 100,2)))+"%"
	else:
		on_hold_perc = "0%"
	if cash_total > 0:
		cash_perc = str(flt(round((cash_total / grand_total) * 100, 2)))+"%"
	else:
		cash_perc = "0%"
	if bank_total > 0:
		bank_perc = str(flt(round((bank_total / grand_total) * 100, 2)))+"%"
	else:
		bank_perc = "0%"

	return on_hold_total, cash_total, bank_total, grand_total, on_hold_perc, cash_perc, bank_perc, on_hold_heads, cash_heads, bank_heads, total_heads

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


