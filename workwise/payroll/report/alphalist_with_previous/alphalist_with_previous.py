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
		#total previous taxable compensation exclude benefits and basic
		prev_taxable_compensation = (d.pt_represent + d.pt_transpo + d.pt_cola + d.pt_housing + d.pt_comm + d.pt_sharing + 
				d.pt_fees + d.pt_hazard + d.pt_overtime + d.pt_other_a + d.pt_other_b + d.pt_other_sa + d.pt_other_sb)

		taxable_compensation = (d.t_represent + d.t_transpo + d.t_cola + d.t_housing + d.t_comm + d.t_sharing + 
				d.t_fees + d.t_hazard + d.t_overtime + d.t_other_a + d.t_other_b + d.t_other_sa + d.t_other_sb)

		data.append({
			"1": seq,
			"2": d.tax_id,
			"3": d.employee_name,
			"4a": '{:0,.2f}'.format( flt(d.gross_compensation,8) ),
			"4b": '{:0,.2f}'.format( flt(d.pnt_benefits,8) ), #prev_ntax_benefits
			"4c": '{:0,.2f}'.format( flt(d.pnt_demi,8) ), #prev_ntax_demi
			"4d": '{:0,.2f}'.format( flt(d.pnt_contrib,8) ), #prev_ntax_contrib
			"4e": '{:0,.2f}'.format( flt(d.pnt_other,8) ), #prev salaries and other forms of compensation
			"4f": '{:0,.2f}'.format( flt(d.prev_non_taxable_total,8) ), #prev_ntax_total
			"4g": '{:0,.2f}'.format( flt(d.pt_basic,8) ),
			"4h": '{:0,.2f}'.format( flt(d.pt_benefits,8) ), #prev_tax_benefits
			"4i": '{:0,.2f}'.format( flt(prev_taxable_compensation,8) ), #prev_tax_other
			"4j": '{:0,.2f}'.format( flt(d.prev_taxable_total,8) ), #prev_tax_total
			"4k": '{:0,.2f}'.format( flt(d.nt_benefits,8) ),
			"4l": '{:0,.2f}'.format( flt(d.nt_demi,8) ),
			"4m": '{:0,.2f}'.format( flt(d.nt_contrib,8) ),
			"4n": '{:0,.2f}'.format( flt(d.nt_other,8) ),
			"4o": '{:0,.2f}'.format( flt(d.non_taxable_total,8) ),  
			"4p": '{:0,.2f}'.format( flt(d.t_basic,8) ),
			"4q": '{:0,.2f}'.format( flt(d.t_benefits,8) ),
			"4r": '{:0,.2f}'.format( flt(taxable_compensation,8) ),
			"4s": '{:0,.2f}'.format( flt(d.taxable_total,8) ),
			"4t": '{:0,.2f}'.format( flt((d.taxable_total + d.prev_taxable_total),8) ), #grand_tax_total
			"7": '{:0,.2f}'.format( flt(0.0,8) ), #grand_tax_total
			"5": '{:0,.2f}'.format( flt(d.tax_due,8) ),
			"6a": '{:0,.2f}'.format( flt(d.prev_withheld_nov, 8)),
			"6b": '{:0,.2f}'.format( flt(d.withheld_nov,8) ),
			"7a": '{:0,.2f}'.format( flt(d.adj_amount_withheld,8) ),
			"7b": '{:0,.2f}'.format( flt(d.adj_over_withheld,8) ),
			"8": '{:0,.2f}'.format( flt(d.adj_withheld,8) ),
		})

	return data


def get_registers(filters):
	registers = frappe.db.sql("""SELECT * FROM `tabAnnualization Register`
		WHERE company=%(company)s AND payroll_year=%(year)s AND with_previous = 1 AND is_terminated = 0 {conditions} """.format( conditions=get_conditions(filters) ), filters, as_dict=1)

	return registers

def get_conditions(filters):
	conditions = []

	if filters.get("employee"):
		conditions.append("employee=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = [
			d.get("1"),
			d.get("2"),
			d.get("3"), 
			# PREVIOUS EMPLOYER
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
			# PRESENT EMPLOYER
			d.get("4k"),
			d.get("4l"),
			d.get("4m"),
			d.get("4n"),
			d.get("4o"),
			d.get("4p"),
			d.get("4q"),
			d.get("4r"),
			d.get("4s"),
			d.get("4t"),
			# TOTALS
			d.get("7"),
			d.get("5"),
			d.get("6a"),
			d.get("6b"),
			d.get("7a"),
			d.get("7b"),
			d.get("8"),
		]

		result.append(row)

	return result

def get_headers(filters, data):
	tax_id = frappe.db.get_value("Company", filters.company, "tax_id")

	data.append({
		"1": "<b> BIR FORM 1604CF - SCHEDULE 7.4 </b>",
	})

	data.append({
		"1": "<b> ALPHALIST OF EMPLOYEES AS OF DECEMBER 31 WITH PREVIOUS EMPLOYER WITHIN THE YEAR </b>",
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
		"4b": "<b> PREVIOUS EMPLOYER </b>",
		"4k": "<b> PRESENT EMPLOYER </b>",
	})

	data.append({
		"4b": "<b> NON-TAXABLE </b>",
		"4g": "<b> TAXABLE </b>",
		"4k": "<b> NON-TAXABLE </b>",
		"4p": "<b> TAXABLE </b>",
		"4t": "<b> TOTAL </b>",
		"6a": "<b> TAX WITHHELD </b>",
		"7a": "<b> YEAR END ADJUSTMENT </b>",
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
		"4k": "<b> 13th MONTH PAY </b>",
		"4l": "<b> DE MINIMIS </b>",
		"4m": "<b> SSS, GSIS, PHIC & </b>",
		"4n": "<b> SALARIES & OTHER </b>",
		"4o": "<b> TOTAL </b>",
		"4p": "<b> BASIC </b>",
		"4q": "<b> 13th MONTH PAY </b>",
		"4r": "<b> SALARIES & OTHER </b>",
		"4s": "<b> TOTAL </b>",
		"4t": "<b> TAXABLE </b>",
		"7": "<b> NET TAXABLE </b>",
		"5":  "<b> TAX DUE </b>",
		"6a": "<b> (Jan. - Nov.) </b>",
		"7a": "<b> AMT WITHHELD </b>",
		"7b": "<b> OVER </b>",
		"8": "<b> AMOUNT OF TAX </b>",
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
		"4j": "<b> (PREVIOUS EMPLOYER) </b>",
		"4k": "<b> & OTHER BENEFITS </b>",
		"4l": "<b> BENEFITS </b>",
		"4m": "<b> PAG-IBIG CONTRIBUTIONS </b>",
		"4n": "<b> FORMS OF </b>",
		"4o": "<b> NON-TAXABLE/EXEMPT </b>",
		"4p": "<b> SALARY </b>",
		"4q": "<b> & OTHER BENEFITS </b>",
		"4r": "<b> FORMS OF </b>",
		"4s": "<b> COMPENSATION </b>",
		"4t": "<b> (PREVIOUS and </b>",
		"7": "<b> COMPESATION </b>",		
		"5": "<b> (Jan. - Dec.) </b>",
		"6a": "<b> PREVIOUS EMPLOYER </b>",
		"6b": "<b> PRESENT EMPLOYER </b>",
		"7a": "<b> & PAID FOR IN </b>",
		"7b": "<b> WITHHELD TAX </b>",
		"8": "<b> WITHHELD AS </b>",
	})

	data.append({
		"2": "<b> NUMBER </b>",
		"4a": "<b> INCOME </b>",
		"4d": "<b> AND UNION DUES </b>",
		"4e": "<b> COMPENSATION </b>",
		"4f": "<b> COMPENSATION INCOME </b>",
		"4i": "<b> COMPENSATION </b>",
		"4m": "<b> AND UNION DUES </b>",
		"4n": "<b> COMPENSATION </b>",
		"4o": "<b> COMPENSATION INCOME </b>",
		"4r": "<b> COMPENSATION </b>",
		"4s": "<b> (PRESENT EMPLOYERS) </b>",
		"4t": "<b> PRESENT EMPLOYERS) </b>",
		"7": " <b> INCOME  </b>",
		"7a": "<b> DECEMBER </b>",
		"7b": "<b> EMPLOYEE </b>",
		"8": "<b> ADJUSTED </b>",
	})	

	data.append({
		"4f": "<b> (PREVIOUS) </b>",
		"4o": "<b> (PRESENT) </b>",
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

		"4k": "<b> 4(k) </b>",
		"4l": "<b> 4(l) </b>",
		"4m": "<b> 4(m) </b>",
		"4n": "<b> 4(n) </b>",
		"4o": "<b> 4(o) </b>",
		"4p": "<b> 4(p) </b>",
		"4q": "<b> 4(q) </b>",
		"4r": "<b> 4(r) </b>",
		"4s": "<b> 4(s) </b>",
		"4t": "<b> 4(t) </b>",


		"7": "<b> (7) </b>",		
		"5":  "<b> (5) </b>",
		"6a": "<b> (6a) </b>",
		"6b":  "<b> (6b) </b>",
	})

def get_columns(filters):
	columns = [
		{
			"fieldname": "1",
			"label": " ",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "2",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "3",
			"label": " ",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "4a",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4b",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4c",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4d",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4e",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4f",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4g",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4h",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4i",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4j",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4k",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4l",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4m",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4n",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4o",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4p",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4q",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4r",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4s",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4t",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "7",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "6a",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "6b",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "7a",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "7b",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "8",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
	]

	return columns