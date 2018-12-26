# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _
from workwise.payroll.payroll_utils import get_transaction_map

def execute(filters=None):
	employee_details = {}
	for emp in frappe.db.sql("""select name, tin, full_name from tabEmployee WHERE company = %(company)s """, filters,as_dict=1):
		employee_details.setdefault(emp.name, emp)

	employees = frappe.db.sql("""select name, tin, full_name from tabEmployee WHERE company = %(company)s """, filters,as_dict=1)

	if not filters: filters = frappe._dict({})
	validate_filters(filters)

	#employees = get_employees(filters)
	columns = get_columns(filters)

	#if not employees:
	#	frappe.throw(_("No record found"))

	columns = get_columns(filters)
	results = get_result(filters, employees, employee_details)

	return columns, results

def get_result(filters, employees, employee_details):
	registers = get_registers(filters)

	data = get_data_with_opening_closing(filters, employees, employee_details, registers)
	result = get_result_as_list(data, filters)

	return result

def get_data_with_opening_closing(filters, employees, employee_details, registers):
	data = []
	emp_map = init_register_map(registers, employees, employee_details)
	emp_map = get_employee_wise_register(filters, registers, emp_map)

	get_headers(filters, data)

	seq = 0
	for emp, emp_dict in emp_map.items():
		seq += 1
		ntax_bonus, tax_bonus  = 0, 0
		ntax_total = 0

		if emp_dict.ntax_bonus > 90000:
			ntax_bonus = 90000
			tax_bonus = (emp_dict.ntax_bonus - 90000		)
		else:
			ntax_bonus = emp_dict.ntax_bonus

		ntax_total = (ntax_bonus + emp_dict.ntax_deminimis + emp_dict.ntax_contribution + emp_dict.ntax_other)
		tax_total = (tax_bonus + emp_dict.tax_basic + emp_dict.tax_other)

		data.append({
			"1": seq,
			"2": emp_dict.tin,
			"3": emp_dict.employee_name,
			"4a": '{:0,.2f}'.format( emp_dict.gross_compensation ),
			"4b": '{:0,.2f}'.format( emp_dict.ntax_bonus ),
			"4c": '{:0,.2f}'.format( emp_dict.ntax_deminimis ),
			"4d": '{:0,.2f}'.format( emp_dict.ntax_contribution ),
			"4e": '{:0,.2f}'.format( emp_dict.ntax_other ),
			"4f": '{:0,.2f}'.format( ntax_total ),  
			"4g": '{:0,.2f}'.format( emp_dict.tax_basic ),
			"4h": '{:0,.2f}'.format( tax_bonus ),
			"4i": '{:0,.2f}'.format( emp_dict.tax_other ),
			"4j": '{:0,.2f}'.format( tax_total ),
			"5a":  "",
			"5b": '{:0,.2f}'.format( 0.0 ),
			"6a": '{:0,.2f}'.format( 0.0 ),
			"5":  '{:0,.2f}'.format( tax_total ),
			"6b": '{:0,.2f}'.format( emp_dict.tax_due ),
			"7": '{:0,.2f}'.format( emp_dict.tax_withheld ),
			"8a": '{:0,.2f}'.format( 0.0 ),
			"8b": '{:0,.2f}'.format( abs(emp_dict.tax_due - emp_dict.tax_withheld) ),
			"9": '{:0,.2f}'.format( emp_dict.tax_withheld - 0.0 ),
			"10": "",
		})

	return data

def get_employee_wise_register(filters, registers, emp_map):
	tr_map = get_transaction_map()
	#test_case = []
	#gross_compensation, amount, net_taxable, tax_due, tax_withheld = 0, 0, 0, 0, 0
	#ntax_bonus, ntax_deminimis, ntax_government, ntax_other, ntax_total = 0, 0, 0, 0, 0
	#tax_basic, tax_bonus, tax_other, tax_total = 0, 0, 0, 0 
	#adj_amount_withheld, adj_over_withheld, adj_withheld = 0, 0, 0
	for reg in registers:
		total_bonus, tax_income, tax_deduction = 0, 0, 0
		#emp_map[reg.employee].gross_compensation += reg.gross_payroll
		if tr_map[reg.pay_code]['type'] == "Income":
			emp_map[reg.employee].gross_compensation += reg.amount
		
		if tr_map[reg.pay_code]['bir_type'] == "13th Month" and not tr_map[reg.pay_code]['type'] == "None":
			emp_map[reg.employee].ntax_bonus += reg.amount

		if tr_map[reg.pay_code]['bir_type'] == "Deminimis" and not tr_map[reg.pay_code]['is_taxable']:
			emp_map[reg.employee].ntax_deminimis += reg.amount

		if tr_map[reg.pay_code]['bir_type'] == "Contribution":
			emp_map[reg.employee].ntax_contribution += reg.amount

		if tr_map[reg.pay_code]['bir_type'] == "Other" and not tr_map[reg.pay_code]['is_taxable']:
			emp_map[reg.employee].ntax_other += reg.amount

		#TAXABLE BASIC SALARY
		if tr_map[reg.pay_code]['bir_type'] == "Basic" and tr_map[reg.pay_code]['type'] == "Income" and tr_map[reg.pay_code]['is_taxable']:
			tax_income += reg.amount
			#if reg.employee == "623":
			#	test_case.append(reg.name)

		if tr_map[reg.pay_code]['bir_type'] == "Basic" and tr_map[reg.pay_code]['type'] == "Deduction" and tr_map[reg.pay_code]['is_taxable']:
			tax_deduction += reg.amount

		if tr_map[reg.pay_code]['bir_type'] == "Contribution" and tr_map[reg.pay_code]['type'] == "Deduction" and tr_map[reg.pay_code]['is_taxable']:
			tax_deduction += reg.amount
		

		emp_map[reg.employee].tax_basic += tax_income - tax_deduction

		#4(I)
		if tr_map[reg.pay_code]['bir_type'] == "Other" and tr_map[reg.pay_code]['is_taxable']:
			emp_map[reg.employee].tax_other += reg.amount

		#(6)
		table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table`
			WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",((tax_income - tax_deduction), (tax_income - tax_deduction), 'Yearly'), as_dict=True )
		tax_due = 0
		for t in table:
			tax_due = (flt( (tax_income - tax_deduction) , 8) - flt(t.compensatory, 8)) * flt(flt(t.percentage, 8) / 100 , 8)
			if t.prescribed > 0:
				tax_due += flt(t.prescribed, 8)
		emp_map[reg.employee].tax_due += tax_due

		#(7)
		if reg.pay_code == "WHTAX":
			emp_map[reg.employee].tax_withheld += reg.amount

	#frappe.throw(_(test_case))
	return emp_map

def get_employees(filters):
	employees = frappe.db.sql(""" SELECT `name` FROM `tabEmployee`  WHERE company = %(company)s """, filters, as_dict=1)

def get_registers(filters):
	registers = frappe.db.sql("""SELECT PR.name, PR.employee, PR.employee_name, PR.company, PR.posting_date, PR.schedule, PR.gross_payroll,
			PRE.pay_code, PRE.entry_type, PRE.is_taxable, PRE.amount FROM `tabPayroll Register` PR
		INNER JOIN `tabPayroll Register Entries` PRE ON PRE.parent = PR.`name`
		WHERE PR.company=%(company)s {conditions} """.format( conditions=get_conditions(filters) ), filters, as_dict=1)

	return registers

def get_conditions(filters):
	conditions = []

	if filters.get("employee"):
		conditions.append("PR.employee=%(employee)s")

	from_year, to_year = frappe.db.get_value("Payroll Year", filters.year, ["from_date", "to_date"])
	#if filters.get("year"):
	#	conditions.append("PR.employee=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def init_register_map(registers, employees, employee_details):
	emp_map = frappe._dict()
	for emp in employees:
		emp_map.setdefault(emp.name, frappe._dict({
				"entries": [],
				"seq": 0,
				"tin": emp.tin,
				"employee": emp.name,
				"employee_name": emp.full_name,
				"gross_compensation": 0,
				#NON-TAXABLE
				"ntax_bonus": 0,
				"ntax_deminimis": 0,
				"ntax_contribution": 0,
				"ntax_other": 0,
				"ntax_total": 0,
				#TAXABLE
				"tax_basic": 0,
				"tax_bonus": 0,
				"tax_other": 0,
				"tax_total": 0,
				#EXEMPTION
				"amount": 0,
				"net_taxable": 0,
				"tax_due": 0,
				"tax_withheld": 0,
				#YEAR END ADJUSTMENT
				"adj_amount_withheld": 0,
				"adj_over_withheld": 0,
				"adj_withheld": 0
			})
		)

	return emp_map

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

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

def get_employees(filters):
	employees = frappe.db.sql("""SELECT `name`, full_name, first_name, middle_name, last_name, tin	FROM tabEmployee
		WHERE company = %(company)s
		AND on_hold = 0 AND is_active = 1 ORDER BY last_name, first_name""", filters, as_dict=1)

	return employees

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("PR.`name`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

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