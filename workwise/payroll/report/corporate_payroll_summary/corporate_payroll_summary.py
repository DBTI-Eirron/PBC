# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)

	PRE_dict = get_PRE_dict(filters)
	PR_dict = get_PR_dict(filters)

	data = []
	for pre in PRE_dict:
		net_pay = (flt(PRE_dict[pre]["BS"]) + flt(PRE_dict[pre]["ND"])) - (flt(PRE_dict[pre]["LT"]) + flt(PRE_dict[pre]["AT"]) + flt(PRE_dict[pre]["UT"]))
		data.append({"company":PRE_dict[pre]["company"],"no_regular":PR_dict[pre]["Regular"],"no_proby":PR_dict[pre]["Probationary"],"no_total":flt(PR_dict[pre]["Regular"]) + flt(PR_dict[pre]["Probationary"]),"days_worked":flt(PR_dict[pre]["worked_days"]),"net_basic":net_pay,"overtime":PRE_dict[pre]["OT"],"total_payroll":net_pay + flt(PRE_dict[pre]["OT"])})
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
			"fieldname": "no_regular",
			"label": _("No. of Regular Employee"),
			"fieldtype": "Data",
			"width": 130
		},{
			"fieldname": "no_proby",
			"label": _("No. of Proby Employee"),
			"fieldtype": "Data",
			"width": 130
		},{
			"fieldname": "no_total",
			"label": _("Total Employee"),
			"fieldtype": "Data",
			"width": 130
		},{
			"fieldname": "days_worked",
			"label": _("Total Days Worked"),
			"fieldtype": "Data",
			"width": 150
		},{
			"fieldname": "net_basic",
			"label": _("Net Basic"),
			"fieldtype": "Currency",
			"width": 150
		},{
			"fieldname": "overtime",
			"label": _("Overtime"),
			"fieldtype": "Currency",
			"width": 150
		},{
			"fieldname": "total_payroll",
			"label": _("Total Payroll"),
			"fieldtype": "Currency",
			"width": 150
		}
	]

	return columns

def get_PRE_dict(filters):
	PRE_entries = frappe.db.sql("""SELECT PR.company, PRE.pay_code, PRE.amount
	FROM `tabPayroll Register` PR 
	INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.parent 
	WHERE (PRE.pay_code = "BS" OR PRE.pay_code = "ND" OR PRE.pay_code = "LT" OR PRE.pay_code = "UT" OR PRE.pay_code = "AT" OR PRE.pay_code = "OT") AND PR.posting_date BETWEEN %s AND %s
	"""+add_condition(filters),(filters.from_date,filters.to_date),as_dict=True)

	PRE_dict = {}

	for entry in PRE_entries:
		if entry.company not in PRE_dict:
			PRE_dict.setdefault(entry.company, frappe._dict({"company":entry.company,"BS":0.00,"ND":0.00,"LT":0.00,"UT":0.00,"AT":0.00,"OT":0.00}))
		PRE_dict[entry.company][entry.pay_code] += entry.amount
	return PRE_dict

def get_PR_dict(filters):
	PR_entries = frappe.db.sql("""SELECT PR.company, TE.employment_status, PR.present_days
	FROM `tabPayroll Register` PR
	INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
	WHERE (TE.employment_status = "Regular" OR TE.employment_status = "Probationary") AND PR.posting_date BETWEEN %s AND %s
	"""+add_condition(filters),(filters.from_date,filters.to_date),as_dict=True)

	PR_dict = {}

	for entry in PR_entries:
		if entry.company not in PR_dict:
			PR_dict.setdefault(entry.company, frappe._dict({"company":entry.company,"Regular":0,"Probationary":0,"worked_days":0}))
		PR_dict[entry.company]["worked_days"] += entry.present_days 
		PR_dict[entry.company][entry.employment_status] += 1

	return PR_dict

def add_condition(filters):
	condition = ""
	if filters.company:
		condition += "AND PR.company = '"+filters.company+"'"
	return condition