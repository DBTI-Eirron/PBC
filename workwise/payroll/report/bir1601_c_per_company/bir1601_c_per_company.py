# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, calendar, time
from frappe.utils import cint, flt, getdate, cstr
from time import strptime
from frappe import _, msgprint
from workwise.payroll.payroll_utils import get_transaction_map, format_precision, format_align_right

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "company",
			"label": _(""),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "compensation",
			"label": _(""),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "statutory",
			"label": _(""),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "holiday_pay",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "13th",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "de_minimis",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "sss_hdmf_phic",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "other_non_taxable",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "total_non_taxable",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "total_taxable",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "less_taxable",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "net_taxable",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "total_wth",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "adjustment",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "taxes_remittance",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
	]

	return columns

def get_data(filters):
	data = []
	company = get_company(filters)
	pay_from,pay_to = get_pay_date(filters)
	data.append({})
	data.append({"company":"Company","compensation":"Total Amount Compensation","statutory":"Statutory Minimum Wage","holiday_pay":"Holiday Pay, Overtime","13th":"13th Month Pay and","de_minimis":"De Minimis Benefits","sss_hdmf_phic":"SSS,PHIC,HDMF","other_non_taxable":"Other Non-Taxable","total_non_taxable":"Total Non Taxable","total_taxable":"Total Taxable","less_taxable":"Less: Taxable","net_taxable":"Net Taxable","total_wth":"Total Taxes Withheld","adjustment":"Add/(Less):Adjustment","taxes_remittance":"Taxes Withheld for"})
	data.append({"statutory":"for Minimum Wage","holiday_pay":"Pay, Night Differential","13th":"other benifits","sss_hdmf_phic":"Mandatory","other_non_taxable":"Compensation","total_non_taxable":"Employees","total_taxable":"Compensation","less_taxable":"Compensation not","net_taxable":"Compensation","adjustment":"of taxes Withheld from","taxes_remittance":"Remittance"})
	data.append({"statutory":"Earners (WWE)","holiday_pay":"Pay, Hazard Pay","sss_hdmf_phic":"Contributions","less_taxable":"subjected to Withholding","adjustment":"Previous Month/s"})
	data.append({})
	for comp in company:
		entries = frappe.db.sql("""
		SELECT
			PR.`name`,
			PRE.amount,
			PRE.pay_code,
			PR.daily_rate,
			PR.total_income,
			PR.taxable_income,
			TT.type,
			TT.bir_type,
			TL.min_wage
		FROM `tabPayroll Register Entries` PRE
		INNER JOIN `tabPayroll Register` PR ON PRE.parent = PR.name
		INNER JOIN `tabTransaction Type` TT ON PRE.pay_code = TT.`code`
		INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		INNER JOIN `tabLocation` TL ON TE.location = TL.`name`
		WHERE TE.company = %(company)s AND PR.posting_date BETWEEN %(from_date)s AND %(to_date)s
		{conditions}
		GROUP BY PRE.`name`""".format(conditions=get_conditions(filters)),{ 
		"company": comp,
		"from_date": getdate(pay_from),
		"to_date": getdate(pay_to),
		}, as_dict=True)
		overtime_pay = holiday_pay = trtnt_month_pay = de_minimis = sss_hdmf_phic = wht = statutory = amount_compensation = taxable_salary = other = night_dif = 0.00
		done = []
		for ent in entries:
			if ent.name not in done:
				amount_compensation += flt(ent.total_income , 8)
				taxable_salary += flt(ent.taxable_income , 8)
				done.append(ent.name)
			if ent.bir_type == "Overtime" and ent.type == "Income":
				holiday_pay	 += ent.amount
			if ent.bir_type == "Overtime" and ent.type == "Deduction":
				holiday_pay	 -= ent.amount
			if ent.bir_type == "Holiday" and ent.type == "Income":
				holiday_pay += ent.amount
			if ent.bir_type == "Holiday" and ent.type == "Deduction":
				holiday_pay -= ent.amount
			if ent.bir_type == "Night Differential" and ent.type == "Income":
				holiday_pay	 += ent.amount
			if ent.bir_type == "Night Differential" and ent.type == "Deduction":
				holiday_pay	 -= ent.amount
			if ent.bir_type == "13th Month" and ent.type == "Income":
				trtnt_month_pay += ent.amount
			if ent.bir_type == "13th Month" and ent.type == "Deduction":
				trtnt_month_pay -= ent.amount
			if ent.bir_type == "Deminimis" and ent.type == "Income":
				de_minimis += ent.amount
			if ent.bir_type == "Deminimis" and ent.type == "Deduction":
				de_minimis -= ent.amount
			if ent.bir_type == "Other" and ent.type == "Income":
				other += ent.amount
			if ent.bir_type == "Other" and ent.type == "Deduction":
				other -= ent.amount
			if ent.pay_code == "SSS":
				sss_hdmf_phic += ent.amount
			if ent.pay_code == "HDMF":
				sss_hdmf_phic += ent.amount
			if ent.pay_code == "PHIC":
				sss_hdmf_phic += ent.amount
			if ent.pay_code == "WHTAX":
				wht += ent.amount
			if ent.daily_rate <= ent.min_wage:
				if ent.bir_type == "Basic" and ent.type == "Income":
					statutory += ent.amount
				if ent.bir_type == "Basic" and ent.type == "Deduction":
					statutory -= ent.amount

		data.append({"company":comp,
			"compensation":format_precision(amount_compensation,filters.value_precision),
			"statutory":format_precision(statutory,filters.value_precision),
			"holiday_pay":format_precision(flt(holiday_pay,8),filters.value_precision),
			"13th":format_precision(trtnt_month_pay,filters.value_precision),
			"de_minimis":format_precision(de_minimis,filters.value_precision),
			"sss_hdmf_phic":format_precision(sss_hdmf_phic,filters.value_precision),
			"other_non_taxable":format_precision(other,filters.value_precision),
			"total_non_taxable":format_precision(flt(statutory,8) + flt(holiday_pay,8) + flt(trtnt_month_pay,8)  + flt(de_minimis,8) + flt(sss_hdmf_phic,8) + flt(other,8),filters.value_precision),
			"total_taxable":format_precision(amount_compensation - (flt(statutory,8) + flt(holiday_pay,8) + flt(trtnt_month_pay,8)  + flt(de_minimis,8) + flt(sss_hdmf_phic,8) + flt(other,8)),filters.value_precision),
			"less_taxable":format_precision(0,filters.value_precision),
			"net_taxable":format_precision(amount_compensation - (flt(statutory,8) + flt(holiday_pay,8) + flt(trtnt_month_pay,8)  + flt(de_minimis,8) + flt(sss_hdmf_phic,8) + flt(other,8)),filters.value_precision),
			"total_wth":format_precision(wht,filters.value_precision),
			"adjustment":format_precision(0,filters.value_precision),
			"taxes_remittance":format_precision(wht,filters.value_precision)
		})
	return data

def get_pay_date(filters):
	pay_from = filters.year+"-"+str(filters.month)+"-01"
	pay_to = filters.year+"-"+str(filters.month)+"-"+str(calendar.monthrange(int(filters.year), int(filters.month))[1])
	pay_from = getdate(str(pay_from))
	pay_to = getdate(str(pay_to))

	return pay_from, pay_to

def get_company(filters):
	company = frappe.db.sql("""SELECT `name` FROM `tabCompany`""",as_dict=True)
	comp_list = []
	for comp in company:
		comp_list.append(comp.name)
	return comp_list

def get_conditions(filters):
	conditions = []
	if frappe.session.user != "Administrator":
		conditions.append(_("TE.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

