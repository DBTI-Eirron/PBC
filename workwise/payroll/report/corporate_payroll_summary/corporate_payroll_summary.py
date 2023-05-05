# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)

	PRE_dict = get_PRE_dict(filters)
	PR_dict = get_PR_dict(filters)

	total_no_regular = 0
	total_no_proby = 0
	total_no_total = 0
	total_days_worked = 0
	total_overtime = 0.00
	total_td = 0.00
	total_ti = 0.00
	total_tp = 0.00

	data = []
	for pre in PR_dict:
		if pre in PRE_dict:
			overtime = PRE_dict[pre]['amount']
		else:
			overtime = 0.00
		total_no_regular += PR_dict[pre]["Regular"]
		total_no_proby += PR_dict[pre]["Probationary"]
		total_no_total += PR_dict[pre]["Regular"] + PR_dict[pre]["Probationary"]
		total_days_worked += PR_dict[pre]["worked_days"]
		total_td += PR_dict[pre]['total_deduction']
		total_tp += PR_dict[pre]['total_income']-PR_dict[pre]['total_deduction']
		total_ti += PR_dict[pre]['total_income']-overtime
		total_overtime += overtime
		data.append({
			"company": PR_dict[pre]["company"],
			"location": PR_dict[pre]["location"],
			"no_regular": PR_dict[pre]["Regular"],
			"no_proby": PR_dict[pre]["Probationary"],
			"no_total": flt(PR_dict[pre]["Regular"]) + flt(PR_dict[pre]["Probationary"]),
			"days_worked": flt(PR_dict[pre]["worked_days"]),
			"overtime": format_precision(overtime, filters.value_precision),
			"total_income": format_precision(PR_dict[pre]['total_income']-overtime, filters.value_precision),
			"total_deduction": format_precision(PR_dict[pre]['total_deduction'], filters.value_precision),
			"total_payroll": format_precision(PR_dict[pre]['total_income']-PR_dict[pre]['total_deduction'], filters.value_precision),
		})
	data.append({
		"company": "",
		"location": "TOTAL",
		"no_regular": total_no_regular,
		"no_proby": total_no_proby,
		"no_total": total_no_total,
		"days_worked": total_days_worked,
		"overtime": format_precision(total_overtime,filters.value_precision),
		"total_income": format_precision(total_ti,filters.value_precision),
		"total_deduction": format_precision(total_td,filters.value_precision),
		"total_payroll": format_precision(total_tp,filters.value_precision),
	})
	
	return columns, data


def get_PRE_dict(filters):
	PRE_entries = frappe.db.sql("""SELECT PR.company, PRE.pay_code, PRE.amount, PR.location
	FROM `tabPayroll Register` PR 
	INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
	INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.parent 
	WHERE (PRE.pay_code = "ND" OR PRE.pay_code = "OT") AND (TE.employment_status = "Regular" OR TE.employment_status = "Probationary") AND PR.posting_date BETWEEN %s AND %s
	"""+add_condition(filters),(filters.from_date,filters.to_date),as_dict=True)
	PRE_dict = {}

	for entry in PRE_entries:
		if cstr(entry.company)+"+"+cstr(entry.location) not in PRE_dict:
			PRE_dict.setdefault(cstr(entry.company)+"+"+cstr(entry.location), frappe._dict({"company":entry.company,"location":entry.location,"amount":0.00}))
		PRE_dict[cstr(entry.company)+"+"+cstr(entry.location)]['amount'] += entry.amount
	return PRE_dict


def get_PR_dict(filters):
	PR_entries = frappe.db.sql("""SELECT PR.company, TE.employment_status, PR.present_days, PR.location, PR.total_income, PR.total_deduction
	FROM `tabPayroll Register` PR
	INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
	WHERE (TE.employment_status = "Regular" OR TE.employment_status = "Probationary") AND PR.posting_date BETWEEN %s AND %s
	"""+add_condition(filters),(filters.from_date,filters.to_date),as_dict=True)

	PR_dict = {}

	for entry in PR_entries:
		if cstr(entry.company)+"+"+cstr(entry.location) not in PR_dict:
			PR_dict.setdefault(cstr(entry.company)+"+"+cstr(entry.location), frappe._dict({"company":entry.company,"location":entry.location,"Regular":0,"Probationary":0,"worked_days":0,"total_income":0,"total_deduction":0}))
		
		employment_status = str(entry.employment_status).title()
		PR_dict[cstr(entry.company)+"+"+cstr(entry.location)]["worked_days"] += entry.present_days 
		PR_dict[cstr(entry.company)+"+"+cstr(entry.location)][employment_status] += 1
		PR_dict[cstr(entry.company)+"+"+cstr(entry.location)]["total_income"] += entry.total_income 
		PR_dict[cstr(entry.company)+"+"+cstr(entry.location)]["total_deduction"] += entry.total_deduction 

	return PR_dict

def add_condition(filters):
	condition = ""
	if filters.company:
		condition += "AND PR.company = '"+filters.company+"'"
	return condition

def get_columns(filters):
	columns = [
		{
			"fieldname": "company",
			"label": _("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"width": 200

		},{
			"fieldname": "location",
			"label": _("Location"),
			"fieldtype": "Data",
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
			"fieldname": "overtime",
			"label": _("Overtime"),
			"fieldtype": "Data",
			"width": 150
		},{
			"fieldname": "total_income",
			"label": _("Total Income"),
			"fieldtype": "Data",
			"width": 150
		},{
			"fieldname": "total_deduction",
			"label": _("Total Deduction"),
			"fieldtype": "Data",
			"width": 150
		},{
			"fieldname": "total_payroll",
			"label": _("Total Payroll"),
			"fieldtype": "Data",
			"width": 150
		}
	]

	return columns