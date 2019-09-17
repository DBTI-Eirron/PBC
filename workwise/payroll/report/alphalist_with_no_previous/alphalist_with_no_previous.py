# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _
from workwise.payroll.payroll_utils import get_transaction_map

def execute(filters=None):
	pay_from, pay_to = frappe.db.get_value("Payroll Year", filters.year, ["from_date", "to_date"])
	if not filters: filters = frappe._dict({})
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_result(filters):
	registers = get_registers(filters)
	data = get_data(filters, registers)
	result = get_result_as_list(data, filters)

	return result

def get_data(filters, registers):
	data = []
	tr_map = get_transaction_map()
	registers = get_registers(filters)

	get_headers(filters, data)
	seq = 0
	for d in registers:
		seq += 1
		data.append({
			"1": seq,
			"2": d.tax_id,
			"3": d.employee_name,
			"4a": '{:0,.2f}'.format( flt(d.gross_compensation,8) ),
			"4b": '{:0,.2f}'.format( flt(d.nt_benefits,8) ),
			"4c": '{:0,.2f}'.format( flt(d.nt_demi,8) ),
			"4d": '{:0,.2f}'.format( flt(d.nt_contrib,8) ),
			"4e": '{:0,.2f}'.format( flt(d.nt_other,8) ),
			"4f": '{:0,.2f}'.format( flt(d.non_taxable_total,8) ),  
			"4g": '{:0,.2f}'.format( flt(d.t_basic,8) ),
			"4h": '{:0,.2f}'.format( flt(d.t_benefits,8) ),
			"4i": '{:0,.2f}'.format( flt(d.t_other,8) ),
			"4j": '{:0,.2f}'.format( flt(d.taxable_total,8) ),
			"5a":  "",
			"5b": '{:0,.2f}'.format( 0.0 ),
			"6a": '{:0,.2f}'.format( 0.0 ),
			"5":  '{:0,.2f}'.format( flt(d.taxable_total,8) ),
			"6b": '{:0,.2f}'.format( flt(d.tax_due,8) ),
			"7": '{:0,.2f}'.format(  flt(d.tax_withheld,8) ),
			"8a": '{:0,.2f}'.format( flt(d.adj_amount_withheld,8) ),
			"8b": '{:0,.2f}'.format( flt(d.adj_over_withheld,8) ),
			"9": '{:0,.2f}'.format( flt(d.adj_withheld,8) ),
			"10": "",
		})

	return data

def get_registers(filters):
	registers = frappe.db.sql("""SELECT * FROM `tabAnnualization Register`
		WHERE company=%(company)s AND payroll_year=%(year)s AND with_previous = 0 {conditions} """.format( conditions=get_conditions(filters) ), filters, as_dict=1)

	return registers

def get_conditions(filters):
	conditions = []

	if filters.get("employee"):
		conditions.append("PR.employee=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_columns(filters):
	columns = [
		{
			"fieldname": "1",
			"label": _(""),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "2",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "3",
			"label": _(""),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "4a",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4b",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4c",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4d",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4e",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4f",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4g",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4h",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4i",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4j",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5a",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5b",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "6a",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "6b",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "7",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "8a",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "8b",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "9",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "10",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
	]

	return columns

def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = [
			d.get("1"),
			d.get("2"),
			d.get("3"), 
			d.get("4a"),
			d.get("4b"),
			d.get("4c"),
			d.get("4d"),
			d.get("4e"),
			d.get("4f"),
			d.get("4g"),
			d.get("4h"),
			d.get("4i"),
			d.get("4j"),
			d.get("5a"),
			d.get("5b"),
			d.get("6a"),
			d.get("5"),
			d.get("6b"),
			d.get("7"),
			d.get("8a"),
			d.get("8b"),
			d.get("9"),
			d.get("10"),
		]

		result.append(row)

	return result

def get_headers(filters, data):
	tax_id = frappe.db.get_value("Company", filters.company, "tax_id")

	data.append({
		"1": "<b> BIR FORM 1604CF - SCHEDULE 7.3 </b>",
	})

	data.append({
		"1": "<b> ALPHALIST OF EMPLOYEES AS OF DECEMBER 31 WITH NO PREVIOUS EMPLOYER WITHIN THE YEAR </b>",
	})	

	data.append({
		"1": "<b> AS OF DECEMBER 31 "+ str(filters.year) +"</b>",
	})	

	data.append({})
	data.append({})	
	
	data.append({
		"1": "<b> TIN: "+ str(tax_id) +"</b>",
	})	
	data.append({
		"1": "<b> WITHHOLDING AGENT'S NAME: "+ str(filters.company) +"</b>",
	})	
	data.append({})
	data.append({
		"4a": "<b> (4) GROSS COMPENSATION INCOME </b>",
	})

	data.append({
		"4b": "<b> NON-TAXABLE </b>",
		"4g": "<b> TAXABLE </b>",
		"5a": "<b> EXEMPTION </b>"
	})

	data.append({
		"1": "<b> SEQ </b>",
		"2": "<b> TAX PAYER </b>",
		"3": "<b> NAME OF EMPLOYEES </b>",
		"4a": "<b> GROSS </b>",
		"4b": "<b> 13th MONTH PAY </b>",
		"4c": "<b> DE MINIMIS </b>",
		"4d": "<b> SSS, GSIS, PHIC & </b>",
		"4e": "<b> SALARIES & OTHER </b>",
		"4f": "<b> TOTAL </b>",
		"4g": "<b> BASIC </b>",
		"4h": "<b> 13th MONTH PAY </b>",
		"4i": "<b> SALARIES & OTHER </b>",
		"4j": "<b> TOTAL TAXABLE </b>",
		"5a": "<b> CODE </b>",
		"5b": "<b> AMOUNT </b>",
		"6a":  "<b> PREMIUM PAID </b>",
		"5":  "<b> NET TAXABLE </b>",
		"6b": "<b> TAX DUE </b>",
		"7": "<b> TAX WITHHELD </b>",
		"8a": "<b> AMT WITHHELD </b>",
		"8b": "<b> OVER </b>",
		"9": "<b> AMOUNT OF TAX </b>",
		"10": "<b> SUBSTITUTED FILING? </b>",
	})

	data.append({
		"1": "<b> NO </b>",
		"2": "<b> IDENTIFICATION </b>",
		"3": "<b> (Last Name, First Name, Middle Name) </b>",
		"4a": "<b> COMPENSATION </b>",
		"4b": "<b> & OTHER BENEFITS </b>",
		"4c": "<b> BENEFITS </b>",
		"4d": "<b> PAG-IBIG CONTRIBUTIONS </b>",
		"4e": "<b> FORMS OF </b>",
		"4f": "<b> NON-TAXABLE/EXEMPT </b>",
		"4g": "<b> SALARY </b>",
		"4h": "<b> & OTHER BENEFITS </b>",
		"4i": "<b> FORMS OF </b>",
		"4j": "<b> COMPENSATION INCOME </b>",
		"6a":  "<b> ON HEALTH </b>",
		"5":  "<b> COMPENSATION </b>",
		"6b": "<b> (Jan. - Dec.) </b>",
		"7": "<b> (Jan. - Nov.) </b>",
		"8a": "<b> & PAID FOR IN </b>",
		"8b": "<b> WITHHELD TAX </b>",
		"9": "<b> WITHHELD AS </b>",
		"10": "<b> YES/NO </b>",
	})

	data.append({
		"2": "<b> NUMBER </b>",
		"4a": "<b> INCOME </b>",
		"4d": "<b> AND UNION DUES </b>",
		"4e": "<b> COMPENSATION </b>",
		"4f": "<b> COMPENSATION INCOME </b>",
		"4i": "<b> COMPENSATION </b>",
		"6a": "<b> AND/OR HOSPITAL </b>",
		"5": "<b> INCOME </b>",
		"8a": "<b>DECEMBER </b>",
		"8b": "<b> EMPLOYEE </b>",
		"9": "<b> ADJUSTED </b>",
	})	

	data.append({
		"6a": "<b> INSURANCE </b>",
	})	

	data.append({
		"1": _("<b> (1) </b>"),
		"2": "<b> (2) </b>",
		"3": "<b> (3) </b>",
		"4a": "<b> 4(a) </b>",
		"4b": "<b> 4(b) </b>",
		"4c": "<b> 4(c) </b>",
		"4d": "<b> 4(d) </b>",
		"4e": "<b> 4(e) </b>",
		"4f": "<b> 4(f) </b>",
		"4g": "<b> 4(g) </b>",
		"4h": "<b> 4(h) </b>",
		"4i": "<b> 4(i) </b>",
		"4j": "<b> 4(j) </b>",
		"5a": "<b> 5(a) </b>",
		"5b": "<b> 5(b) </b>",
		"6a":  "<b> (6) </b>",
		"5":  "<b> (5) </b>",
		"6b": "<b> (6) </b>",
		"7": "<b> (7) </b>",
		"8a": "<b> 8(a) </b>",
		"8b": "<b> 8(b) </b>",
		"9": "<b> (9) </b>",
		"10": "<b> (10) </b>",
	})