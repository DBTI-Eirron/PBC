# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _
from workwise.payroll.payroll_utils import get_transaction_map

def execute(filters=None):
	employees = frappe.db.sql("""select `name`, tin, full_name from tabEmployee 
			WHERE company = %(company)s and payroll_schedule = %(schedule)s 
			and `name` IN (SELECT DISTINCT employee FROM `tabBIR2316` WHERE document_type = "Previous" AND docstatus = 1) {conditions} """.format( conditions=get_employee_conditions(filters) ), filters, as_dict=1)
	pay_from, pay_to = frappe.db.get_value("Payroll Year", filters.year, ["from_date", "to_date"])

	if not filters: filters = frappe._dict({})

	columns = get_columns(filters)
	results = get_result(filters, employees)

	return columns, results

def get_result(filters, employees):
	registers = get_registers(filters)
	gross_registers = get_gross_registers(filters)
	bir_registers = get_bir_registers(filters)

	data = get_data_with_opening_closing(filters, employees, registers, gross_registers, bir_registers)
	result = get_result_as_list(data, filters)

	return result

def get_data_with_opening_closing(filters, employees, registers, gross_registers, bir_registers):
	data = []
	tr_map = get_transaction_map()
	emp_map = init_register_map(registers, employees)
	emp_map = get_employee_wise_register(filters, registers, gross_registers, emp_map, tr_map)
	emp_map = get_employee_wise_bir(filters, bir_registers, emp_map, tr_map)

	get_headers(filters, data)
	seq = 0
	for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
		seq += 1
		tax_due, amt_withheld, over_withheld, withheld = 0, 0, 0, 0

		#PREVIOUS
		prev_ntax_bonus, prev_tax_bonus, prev_ntax_total = 0, 0, 0
		prev_ntax_total = (emp_dict.prev_ntax_bonus + emp_dict.prev_ntax_deminimis + emp_dict.prev_ntax_contribution + emp_dict.prev_ntax_other)
		prev_tax_total = (prev_tax_bonus + emp_dict.prev_tax_basic + emp_dict.prev_tax_other)

		#PRESENT
		ntax_bonus, tax_bonus, ntax_total = 0, 0, 0
		if emp_dict.ntax_bonus > 90000:
			ntax_bonus = 90000
			tax_bonus = (emp_dict.ntax_bonus - 90000		)
		else:
			ntax_bonus = emp_dict.ntax_bonus

		ntax_total = (ntax_bonus + emp_dict.ntax_deminimis + emp_dict.ntax_contribution + emp_dict.ntax_other)
		tax_total = (tax_bonus + emp_dict.tax_basic + emp_dict.tax_other)

		#TOTAL TAXABLECOMPENSATION
		grand_tax_total = prev_tax_total + tax_total

		#TAX DUE
		table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table`
			WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",(( grand_tax_total ), ( grand_tax_total ), 'Yearly'), as_dict=True )
		for t in table:
			tax_due = (flt( ( grand_tax_total ) , 8) - flt(t.compensatory, 8)) * flt(flt(t.percentage, 8) / 100 , 8)
			if t.prescribed > 0:
				tax_due += flt(t.prescribed, 8)	

		#AMT WITHHELD IN DECEMBER
		withheld = tax_due - ( emp_dict.tax_withheld + emp_dict.prev_tax_withheld)
		if withheld > 1:
			amt_withheld = abs(withheld)
		else:	
			over_withheld = abs(withheld)

		#APPEND DATA
		data.append({
			"1": seq,
			"2": emp_dict.tin,
			"3": emp_dict.employee_name,
			"4a": '{:0,.2f}'.format( emp_dict.gross_compensation ),
			"4b": '{:0,.2f}'.format( emp_dict.prev_ntax_bonus ),
			"4c": '{:0,.2f}'.format( emp_dict.prev_ntax_deminimis ),
			"4d": '{:0,.2f}'.format( emp_dict.prev_ntax_contribution ),
			"4e": '{:0,.2f}'.format( emp_dict.prev_ntax_other ),
			"4f": '{:0,.2f}'.format( prev_ntax_total ),
			"4g": '{:0,.2f}'.format( emp_dict.prev_tax_basic ),
			"4h": '{:0,.2f}'.format( emp_dict.prev_tax_bonus ),
			"4i": '{:0,.2f}'.format( emp_dict.prev_tax_other ),
			"4j": '{:0,.2f}'.format( prev_tax_total ),
			"4k": '{:0,.2f}'.format( emp_dict.ntax_bonus ),
			"4l": '{:0,.2f}'.format( emp_dict.ntax_deminimis ),
			"4m": '{:0,.2f}'.format( emp_dict.ntax_contribution ),
			"4n": '{:0,.2f}'.format( emp_dict.ntax_other ),
			"4o": '{:0,.2f}'.format( ntax_total ),  
			"4p": '{:0,.2f}'.format( emp_dict.tax_basic ),
			"4q": '{:0,.2f}'.format( tax_bonus ),
			"4r": '{:0,.2f}'.format( emp_dict.tax_other ),
			"4s": '{:0,.2f}'.format( tax_total ),
			"4t": '{:0,.2f}'.format( grand_tax_total ),
			"7": '{:0,.2f}'.format( grand_tax_total ),
			"5": '{:0,.2f}'.format( tax_due ),
			"6a": '{:0,.2f}'.format( emp_dict.prev_tax_withheld ),
			"6b": '{:0,.2f}'.format( emp_dict.tax_withheld ),
			"7a": '{:0,.2f}'.format( amt_withheld ),
			"7b": '{:0,.2f}'.format( over_withheld ),
			"8": '{:0,.2f}'.format( abs(withheld)  ),
		})

	return data

def get_employee_wise_register(filters, registers, gross_registers, emp_map, tr_map):
	for gross in gross_registers:
		if gross.employee in emp_map:
			#GROSS COMPENSATION
			emp_map[gross.employee].gross_compensation += gross.gross_payroll

	for reg in registers:
		if reg.employee in emp_map:
			if reg.pay_code in tr_map:
				total_bonus, tax_income, tax_deduction = 0, 0, 0
				#GROSS COMPENSATION
				#if tr_map[reg.pay_code]['type'] == "Income":
				#	emp_map[reg.employee].gross_compensation += reg.amount
				
				#NON-TAXABLE 13TH MONTH & OTHER BENEFITS
				if tr_map[reg.pay_code]['bir_type'] == "13th Month" and not tr_map[reg.pay_code]['type'] == "None":
					emp_map[reg.employee].ntax_bonus += reg.amount

				#DEMINIMIS BENEFITS
				if tr_map[reg.pay_code]['bir_type'] == "Deminimis" and not tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].ntax_deminimis += reg.amount

				# SSS, HDMF, PHIC & UNION DUES
				if tr_map[reg.pay_code]['bir_type'] == "Contribution":
					emp_map[reg.employee].ntax_contribution += reg.amount

				#NON-TAXABLE SALARIES AND OTHER OF COMPENSATION
				if tr_map[reg.pay_code]['bir_type'] == "Other" and tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].ntax_other += reg.amount

				if tr_map[reg.pay_code]['bir_type'] == "Hazard" and tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].tax_other += reg.amount

				if tr_map[reg.pay_code]['bir_type'] == "Overtime" and tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].tax_other += reg.amount

				if tr_map[reg.pay_code]['bir_type'] == "Night Differential" and tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].tax_other += reg.amount

				#TAXABLE BASIC SALARY
				if tr_map[reg.pay_code]['bir_type'] == "Basic" and tr_map[reg.pay_code]['type'] == "Income" and tr_map[reg.pay_code]['is_taxable']:
					tax_income += reg.amount

				if tr_map[reg.pay_code]['bir_type'] == "Basic" and tr_map[reg.pay_code]['type'] == "Deduction" and tr_map[reg.pay_code]['is_taxable']:
					tax_deduction += reg.amount

				if tr_map[reg.pay_code]['bir_type'] == "Contribution" and tr_map[reg.pay_code]['type'] == "Deduction" and tr_map[reg.pay_code]['is_taxable']:
					tax_deduction += reg.amount
				
				emp_map[reg.employee].tax_basic += tax_income - tax_deduction

				#TAXABLE 13TH MONTH AND OTHER BENEFITS
				if tr_map[reg.pay_code]['bir_type'] == "Other" and tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].tax_other += reg.amount

				#TAXABLE SALARIES AND OTHER OF COMPENSATION
				if tr_map[reg.pay_code]['bir_type'] == "Hazard" and tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].tax_other += reg.amount

				if tr_map[reg.pay_code]['bir_type'] == "Overtime" and tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].tax_other += reg.amount

				if tr_map[reg.pay_code]['bir_type'] == "Profit Sharing" and tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].tax_other += reg.amount

				if tr_map[reg.pay_code]['bir_type'] == "Housing Allowance" and tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].tax_other += reg.amount

				if tr_map[reg.pay_code]['bir_type'] == "COLA" and tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].tax_other += reg.amount

				if tr_map[reg.pay_code]['bir_type'] == "Representation" and tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].tax_other += reg.amount

				if tr_map[reg.pay_code]['bir_type'] == "Transportation" and tr_map[reg.pay_code]['is_taxable']:
					emp_map[reg.employee].tax_other += reg.amount

				#TAX DUE
				if tr_map[reg.pay_code]['bir_type'] == "TAX":
					emp_map[reg.employee].tax_withheld += reg.amount
			#else:
			#	frappe.throw("Cannot Generate Alphalist for Year {0} Missing Transaction Type {1} ".format( filters.year, reg.pay_code ))

	return emp_map

def get_employee_wise_bir(filters, bir_registers, emp_map, tr_map):
	
	for reg in bir_registers:
		if reg.employee in emp_map:
			#NON-TAXABLE 13TH MONTH AND OTHER BENEFITS
			emp_map[reg.employee].prev_ntax_bonus += reg.ntax_bonus
			# SSS, HDMF, PHIC & UNION DUES
			emp_map[reg.employee].prev_ntax_contribution += reg.ntax_contrib
			#DEMINIMIS BENEFITS
			emp_map[reg.employee].prev_ntax_deminimis += reg.ntax_demi
			#NON-TAXABLE SALARIES AND OTHER OF COMPENSATION
			emp_map[reg.employee].prev_ntax_other += reg.ntax_bs
			emp_map[reg.employee].prev_ntax_other += reg.ntax_hazard
			emp_map[reg.employee].prev_ntax_other += reg.ntax_ho
			emp_map[reg.employee].prev_ntax_other += reg.ntax_nd		
			emp_map[reg.employee].prev_ntax_other += reg.ntax_ot	
			emp_map[reg.employee].prev_ntax_other += reg.ntax_other

			#TAXABLE BASIC SALARY
			emp_map[reg.employee].prev_tax_basic += reg.tax_bs 
			#TAXABLE 13TH MONTH AND OTHER BENEFITS
			emp_map[reg.employee].prev_tax_bonus += reg.tax_bonus
			#TAXABLE SALARIES AND OTHER OF COMPENSATION
			emp_map[reg.employee].prev_tax_other += reg.tax_rep 
			emp_map[reg.employee].prev_tax_other += reg.tax_transpo 
			emp_map[reg.employee].prev_tax_other += reg.tax_cola
			emp_map[reg.employee].prev_tax_other += reg.tax_housing
			emp_map[reg.employee].prev_tax_other += reg.tax_commission
			emp_map[reg.employee].prev_tax_other += reg.tax_sharing
			emp_map[reg.employee].prev_tax_other += reg.tax_fees		
			emp_map[reg.employee].prev_tax_other += reg.tax_ot	

			emp_map[reg.employee].prev_tax_withheld += ( reg.sum_atw_pres + reg.sum_atw_prev )

	return emp_map

def get_employees(filters):
	employees = frappe.db.sql(""" SELECT `name` FROM `tabEmployee` WHERE company = %(company)s and payroll_schedule = %(schedule)s """, filters, as_dict=1)

def get_registers(filters):
	registers = frappe.db.sql("""SELECT PR.name, PR.employee, PR.employee_name, PR.company, PR.posting_date, PR.schedule, PR.gross_payroll,
			PRE.pay_code, PRE.entry_type, PRE.is_taxable, PRE.amount FROM `tabPayroll Register` PR
		INNER JOIN `tabPayroll Register Entries` PRE ON PRE.parent = PR.`name`
		WHERE PR.company=%(company)s AND PR.schedule=%(schedule)s {conditions} """.format( conditions=get_conditions(filters) ), filters, as_dict=1)

	return registers

def get_gross_registers(filters):
	gross_registers = frappe.db.sql("""SELECT name, employee, gross_payroll FROM `tabPayroll Register`
		WHERE company=%(company)s AND schedule=%(schedule)s {conditions} """.format( conditions=get_conditions(filters) ), filters, as_dict=1)

	return gross_registers

def get_bir_registers(filters):
	bir_registers = frappe.db.sql("""SELECT BIR.* FROM `tabBIR2316` BIR
		INNER JOIN `tabEmployee` EMP ON EMP.`name` = BIR.employee 
		WHERE EMP.company=%(company)s AND BIR.document_type = "Previous" AND BIR.payroll_year=%(year)s {conditions} AND BIR.docstatus = 1 """.format( conditions=get_bir_conditions(filters) ), filters, as_dict=1)

	return bir_registers	

def get_conditions(filters):
	conditions = []

	if filters.get("employee"):
		conditions.append("employee=%(employee)s")

	from_year, to_year = frappe.db.get_value("Payroll Year", filters.year, ["from_date", "to_date"])
	if from_year:
		conditions.append( "posting_date >= '{0}' ".format(from_year) )

	if to_year:
		conditions.append( "posting_date <= '{0}' ".format(to_year) )

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_employee_conditions(filters):
	conditions = []

	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_bir_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("employee=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def init_register_map(registers, employees):
	emp_map = frappe._dict()
	for emp in employees:
		emp_map.setdefault(emp.name, frappe._dict({
				"entries": [],
				"seq": 0,
				"tin": emp.tin,
				"employee": emp.name,
				"employee_name": emp.full_name,
				"gross_compensation": 0,
				#PREVIOUS NON-TAXABLE
				"prev_ntax_bonus": 0,
				"prev_ntax_deminimis": 0,
				"prev_ntax_contribution": 0,
				"prev_ntax_other": 0,
				"prev_ntax_total": 0,
				#PREVIOUS TAXABLE
				"prev_tax_basic": 0,
				"prev_tax_bonus": 0,
				"prev_tax_other": 0,
				"prev_tax_total": 0,				
				#PRESENT NON-TAXABLE
				"ntax_bonus": 0,
				"ntax_deminimis": 0,
				"ntax_contribution": 0,
				"ntax_other": 0,
				"ntax_total": 0,
				#PRESENT TAXABLE
				"tax_basic": 0,
				"tax_bonus": 0,
				"tax_other": 0,
				"tax_total": 0,
				#EXEMPTION
				"amount": 0,
				"net_taxable": 0,
				"tax_due": 0,
				"tax_withheld": 0,
				"prev_tax_withheld": 0,
				#YEAR END ADJUSTMENT
				"adj_amount_withheld": 0,
				"adj_over_withheld": 0,
				"adj_withheld": 0
			})
		)

	return emp_map

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
			"fieldname": "4k",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4l",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4m",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4n",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4o",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4p",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4q",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4r",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4s",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "4t",
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
			"fieldname": "5",
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
			"fieldname": "6b",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "7a",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "7b",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "8",
			"label": _(""),
			"fieldtype": "Data",
			"width": 120
		},
	]

	return columns