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
			"5a": '{:0,.2f}'.format( flt(d.prev_gross_compensation,8) ),
			"5b": '{:0,.2f}'.format( flt(d.pnt_basic,8) ), 
			"5c": '{:0,.2f}'.format( flt(d.pnt_holiday,8) ), 
			"5d": '{:0,.2f}'.format( flt(d.pnt_overtime,8) ),
			"5e": '{:0,.2f}'.format( flt(d.pnt_nightdiff,8) ),
			"5f": '{:0,.2f}'.format( flt(d.pnt_hazard,8) ),
			"5g": '{:0,.2f}'.format( flt(d.pnt_benefits,8) ),
			"5h": '{:0,.2f}'.format( flt(d.pnt_demi,8) ),
			"5i": '{:0,.2f}'.format( flt(d.pnt_contrib,8) ),
			"5j": '{:0,.2f}'.format( flt(d.pnt_other,8) ),
			"5k": '{:0,.2f}'.format( flt(d.prev_non_taxable_total,8) ),

			"5l": '{:0,.2f}'.format( flt(d.t_benefits,8) ),
			"5m": '{:0,.2f}'.format( flt(prev_taxable_compensation,8) ),
			"5n": '{:0,.2f}'.format( flt(d.t_benefits + prev_taxable_compensation,8) ),

			"5o":  d.from_date,  
			"5p":  d.to_date,

			"5q": '{:0,.2f}'.format( flt(d.gross_compensation,8) ),
			"5r": '{:0,.2f}'.format( flt( 0,8) ),
			"5s": '{:0,.2f}'.format( flt( 0,8) ),
			"5t": '{:0,.2f}'.format( flt( 0,8) ),
			"5u": '{:0,.2f}'.format( flt( d.factor, 8) ),
			"5v": '{:0,.2f}'.format( flt( d.nt_holiday,8) ),
			"5w": '{:0,.2f}'.format( flt( d.nt_overtime,8) ),
			"5x": '{:0,.2f}'.format( flt( d.nt_nightdiff,8) ),
			"5y": '{:0,.2f}'.format( flt( d.nt_hazard,8) ),
			"5z": '{:0,.2f}'.format( flt( d.nt_benefits,8) ),
			"5aa": '{:0,.2f}'.format( flt( d.nt_demi,8) ),
			"5ab": '{:0,.2f}'.format( flt( d.nt_contrib,8) ),
			"5ac": '{:0,.2f}'.format( flt( d.nt_other,8) ),
			"5ad": '{:0,.2f}'.format( flt( d.t_benefits) ),
			"5ae": '{:0,.2f}'.format( flt( taxable_compensation) ),
			"5af": '{:0,.2f}'.format( flt( taxable_compensation + d.t_benefits,8) ),
			"5ag": '{:0,.2f}'.format( flt( ( d.t_benefits + prev_taxable_compensation + taxable_compensation + d.t_benefits,8) )),
			"6": '{:0,.2f}'.format( flt(0.0,8) ),
			"7": '{:0,.2f}'.format( flt(d.tax_due,8) ),
			"8a": '{:0,.2f}'.format( flt(d.prev_withheld_nov, 8)),
			"8b": '{:0,.2f}'.format( flt(d.withheld_nov,8) ),
			"9a": '{:0,.2f}'.format( flt(d.adj_amount_withheld,8) ),
			"9b": '{:0,.2f}'.format( flt(d.adj_over_withheld,8) ),
			"10": '{:0,.2f}'.format( flt(d.adj_withheld,8) ),
		})

	return data


def get_registers(filters):
	registers = frappe.db.sql("""SELECT * FROM `tabAnnualization Register`
		WHERE company=%(company)s AND payroll_year=%(year)s AND minimum_wage = 1 AND is_terminated = 0 {conditions} """.format( conditions=get_conditions(filters) ), filters, as_dict=1)

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
			d.get("4"),
			d.get("5a"),
			d.get("5b"),
			d.get("5c"),
			d.get("5d"),
			d.get("5e"),
			d.get("5f"),
			d.get("5g"),
			d.get("5h"),
			d.get("5i"),
			d.get("5j"),
			# PRESENT EMPLOYER
			d.get("5k"),
			d.get("5l"),
			d.get("5m"),
			d.get("5n"),
			d.get("5o"),
			d.get("5p"),
			d.get("5q"),
			d.get("5r"),
			d.get("5s"),
			d.get("5t"),
			d.get("5u"),
			d.get("5v"),
			d.get("5w"),
			d.get("5x"),
			d.get("5y"),
			d.get("5z"),
			d.get("5aa"),
			d.get("5ab"),
			d.get("5ac"),
			d.get("5ad"),
			d.get("5ae"),
			d.get("5ag"),
			# TOTALS
			d.get("6"),
			d.get("7"),
			d.get("8a"),
			d.get("8b"),
			d.get("9a"),
			d.get("9b"),
			d.get("10"),
		]

		result.append(row)

	return result

def get_headers(filters, data):
	tax_id = frappe.db.get_value("Company", filters.company, "tax_id")

	data.append({
		"1": "<b> BIR FORM 1604CF - SCHEDULE 7.5 </b>",
	})

	data.append({
		"1": "<b> ALPHALIST OF MINIMUM WAGE EARNERS </b>",
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
		"5a": "<b> (5) GROSS COMPENSATION INCOME </b>",
		"5o": "<b> (5) GROSS COMPENSATION INCOME </b>",
	})

	data.append({
		"5a": "<b> PREVIOUS EMPLOYER </b>",
		"5o": "<b> PRESENT EMPLOYER </b>",
	})

	data.append({
		"5a": "<b> NON-TAXABLE </b>",
		"5l": "<b> TAXABLE </b>",
		"5o": "<b> NON-TAXABLE </b>",
		"5ad": "<b> TAXABLE </b>",
		"5af": "<b> TOTAL </b>",
		"5ag": "<b> TOTAL COMPENSATION </b>",
		"8a": "<b> TAX WITHHELD </b>",
		"9a": "<b> YEAR END ADJUSTMENT </b>",
	})

	data.append({
		"1": "<b> SEQ </b>",
		"2": "<b> TAX PAYER </b>",
		"3": "<b> NAME OF EMPLOYEES </b>",
		"4": "<b> REGION NO. </b>",
		"5a": "<b> GROSS </b>",
		"5b": "<b> BASIC/ </b>",
		"5c": "<b> HOLIDAY </b>",
		"5d": "<b> OVERTIME </b>",
		"5e": "<b> NIGHT </b>",
		"5f": "<b> HAZARD </b>",
		"5g": "<b> 13th MONTH PAY </b>",
		"5h": "<b> DE MINIMIS </b>",
		"5i": "<b> SSS, GSIS, PHIC & </b>",
		"5j": "<b> SALARIES & OTHER </b>",
		"5k": "<b> TOTAL </b>",
		"5l": "<b> 13th MONTH PAY </b>",
		"5m": "<b> SALARIES & OTHER </b>",
		"5n": "<b> TOTAL TAXABLE </b>",
		"5q": "<b> GROSS </b>",
		"5r": "<b> BASIC SMW </b>",
		"5s": "<b> BASIC SMW </b>",
		"5t": "<b> BASIC SMW </b>",
		"5u": "<b> FACTOR USED </b>",
		"5v": "<b> HOLIDAY </b>",
		"5w": "<b> OVERTIME </b>",		
		"5x": "<b> NIGHT </b>",
		"5y": "<b> HAZARD </b>",
		"5z": "<b> 13th MONTH PAY </b>",

		"5aa": "<b> DE MINIMIS </b>",
		"5ab": "<b> SSS, GSIS, PHIC & </b>",
		"5ac": "<b> SALARIES & OTHER </b>",		
		"5ad": "<b> 13th MONTH PAY </b>",
		"5ae": "<b> SALARIES & OTHER </b>",
		"5af": "<b> COMPENSATION </b>",
		"5ag": "<b> 13th MONTH PAY </b>",


		"6": "<b> NET TAXABLE </b>",
		"7":  "<b> TAX DUE </b>",
		"8a": "<b> (Jan. - Nov.) </b>",
		"9a": "<b> AMT WITHHELD </b>",
		"9b": "<b> OVER </b>",
		"10": "<b> AMOUNT OF TAX </b>",
	})

	data.append({
		"1": "<b> NO </b>",
		"2": "<b> IDENTIFICATION </b>",
		"3": "<b> (Last Name, First Name, Middle Name) </b>",
		"4": "<b> WHERE </b>",
		"5a": "<b> COMPENSATION </b>",
		"5b": "<b> SMW </b>",
		"5c": "<b> PAY </b>",
		"5d": "<b> PAY </b>",
		"5e": "<b> SHIFT </b>",
		"5f": "<b> PAY </b>",
		"5g": "<b> & OTHER BENEFITS </b>",
		"5h": "<b> BENEFITS </b>",
		"5i": "<b> PAG-IBIG CONTRIBUTIONS </b>",
		"5j": "<b> FORMS OF </b>",
		"5k": "<b> NON-TAXABLE/EXEMPT </b>",
		"5l": "<b> & OTHER BENEFITS </b>",
		"5m": "<b> FORMS OF </b>",
		"5n": "<b> (PREVIOUS EMPLOYER) </b>",
		"5o": "<b> EMPLOYEMENT </b>",
		"5q": "<b> COMPENSATION </b>",
		"5r": "<b> PER DAY </b>",
		"5s": "<b> PER MONTH </b>",
		"5t": "<b> PER YEAR </b>",
		"5u": "<b> (NO OF DAYS/YEAR) </b>",
		"5v": "<b> PAY </b>",
		"5w": "<b> PAY </b>",		
		"5x": "<b> SHIFT </b>",
		"5y": "<b> PAY </b>",
		"5z": "<b> & OTHER BENEFITS </b>",


		"5aa": "<b> BENEFITS </b>",
		"5ab": "<b> PAG-IBIG CONTRIBUTIONS </b>",
		"5ac": "<b> FORMS OF </b>",		
		"5ad": "<b> & OTHER BENEFITS </b>",
		"5ae": "<b> FORMS OF </b>",
		"5af": "<b> PRESENT </b>",
		"5ag": "<b> (PREVIOUS AND </b>",

		"6": "<b> COMPESATION </b>",		
		"7": "<b> (Jan. - Dec.) </b>",
		"8a": "<b> PREVIOUS EMPLOYER </b>",
		"8b": "<b> PRESENT EMPLOYER </b>",
		"9a": "<b> & PAID FOR IN </b>",
		"9b": "<b> WITHHELD TAX </b>",
		"10": "<b> WITHHELD AS </b>",
	})

	data.append({
		"2": "<b> NUMBER </b>",
		"4": "<b> ASSIGNED </b>",
		"5a": "<b> PREVIOUS </b>",
		"5e": "<b> DIFFERENTIAL </b>",
		"5i": "<b> AND UNION DUES </b>",
		"5j": "<b> COMPENSATION </b>",
		"5k": "<b> COMPENSATION INCOME </b>",
		"5m": "<b> COMPENSATION </b>",
		"5n": "<b> COMPENSATION </b>",
		"5o": "<b> From </b>",
		"5p": "<b> To </b>",
		"5q": "<b> PRESENT </b>",
		"5x": "<b> DIFFERENTIAL </b>",

		"5ab": "<b> AND UNION DUES </b>",
		"5ac": "<b> COMPENSATION </b>",		
		"5ae": "<b> COMPENSATION </b>",
		"5ag": "<b> PRESENT EMPLOYERS) </b>",

		"7": " <b> INCOME  </b>",
		"9a": "<b> DECEMBER </b>",
		"97b": "<b> EMPLOYEE </b>",
		"10": "<b> ADJUSTED </b>",
	})	

	data.append({
		"4o": "<b> (PRESENT) </b>",
	})	

	data.append({
		"1": _("<b> (1) </b>"),
		"2": "<b> (2) </b>",
		"3": "<b> (3) </b>",
		"4": "<b> (4) </b>",
		"5a": "<b> 5(a) </b>",
		"5b": "<b> 5(b) </b>",
		"5c": "<b> 5(c) </b>",
		"5d": "<b> 5(d) </b>",
		"5e": "<b> 5(e) </b>",
		"5f": "<b> 5(f) </b>",
		"5g": "<b> 5(g) </b>",
		"5h": "<b> 5(h) </b>",
		"5i": "<b> 5(i) </b>",
		"5j": "<b> 5(j) </b>",
		"5k": "<b> 5(k) </b>",
		"5l": "<b> 5(l) </b>",
		"5m": "<b> 5(m) </b>",
		"5n": "<b> 5(n) </b>",
		"5o": "<b> 5(o) </b>",
		"5p": "<b> 5(p) </b>",
		"5q": "<b> 5(q) </b>",
		"5r": "<b> 5(r) </b>",
		"5s": "<b> 5(s) </b>",
		"5t": "<b> 5(t) </b>",
		"5u": "<b> 5(u) </b>",
		"5v": "<b> 5(v) </b>",
		"5w": "<b> 5(w) </b>",		
		"5x": "<b> 5(x) </b>",
		"5y": "<b> 5(y) </b>",
		"5z": "<b> 5(z) </b>",

		"5aa": "<b> 5(aa) </b>",
		"5ab": "<b> 5(ab) </b>",
		"5ac": "<b> 5(ac) </b>",
		"5ad": "<b> 5(ad) </b>",		
		"5ae": "<b> 5(ae) </b>",
		"5af": "<b> 5(af) </b>",
		"5ag": "<b> 5(ag) </b>",		

		"6": "<b> (6) </b>",		
		"7":  "<b> (7) </b>",
		"8a": "<b> (8a) </b>",		
		"8b":  "<b> (8b) </b>",
		"9a": "<b> (9a)=(7)-(8a+8b) </b>",
		"9b":  "<b> ((9b)=(8a+8b)-(7) </b>",
		"10": "<b> (10)=(8+9a)or(8b-9b) </b> "
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
			"fieldname": "4",
			"label": " ",
			"fieldtype": "Data",
			"width": 200
		},		
		{
			"fieldname": "5a",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5b",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5c",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5d",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5e",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5f",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5g",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5h",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5i",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5j",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5k",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5l",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5m",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5n",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5o",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5p",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5q",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5r",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5s",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5t",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5u",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},	
		{
			"fieldname": "5v",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5w",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5x",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5y",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5z",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5aa",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5ab",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5ac",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5ad",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "5ae",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},	
		{
			"fieldname": "5af",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},	
		{
			"fieldname": "5ag",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},	
		{
			"fieldname": "6",
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
			"fieldname": "8a",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "8b",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "9a",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "9b",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "10",
			"label": " ",
			"fieldtype": "Data",
			"width": 120
		},
	]

	return columns