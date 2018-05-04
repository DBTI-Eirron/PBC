from __future__ import unicode_literals
import frappe, datetime
from datetime import time, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _

def get_income(d, freq):
	amount = 0
	if d.income_freq == freq or d.freq == 'Both':
		amount = flt(d.income_rate, 2)

	return {
		"pay_desc": d.income_type,
		"pay_code": d.code,
		"amount": flt(amount, 2),
		"employer_amount": 0.0,
		"compensation": 0.0,
		"source": "Employee",
		"account": d.account,
		"cost_center": "",
		"is_taxable": d.is_taxable,
	}

def get_deduction(d, freq):
	amount = 0
	if d.deduction_freq == freq or d.freq == 'Both':
		amount = flt(d.deduction_rate, 2)
		if freq == 'Both':
			amount = d.deduction_rate / 2 

	return {
		"pay_desc": d.deduction_type,
		"pay_code": d.code,
		"amount": flt(amount, 2),
		"employer_amount": 0.0,
		"compensation": 0.0,
		"source": "Employee",
		"account": d.account,
		"cost_center": "",
		"is_taxable": 0,
	}

def get_sss(d, freq, salary):
	amount = 0
	e_amount = 0
	ec = 0

	if freq == d["sss_freq"] or freq == "Both":
		if d['sss_mode'] == "Manual":
			amount = flt(d["sss_manual"], 2)

		elif d['sss_mode'] == "Table":
			table_amount = frappe.db.sql("""SELECT employee, employer, ec FROM `tabSSS Table`
				WHERE %s >= beginning AND %s <= ending LIMIT 1 """,(salary, salary), as_dict=True )
			
			if table_amount:
				for t in table_amount:
					amount = t.employee
					e_amount = t.employer
					ec = t.ec
		
		if d['sss_freq'] == "Both":
			amount = amount / 2 
			e_amount = e_amount / 2
			ec = t.ec / 2 
	
	return {
		"pay_desc": "SSS",
		"pay_code": "SSS",
		"amount": flt(amount, 2),
		"source": "Deduction",
		"employer_amount": flt(e_amount, 2),
		"compensation": flt(ec, 2),
		"account": "",
		"cost_center": "",
		"is_taxable": 0,
	}

def get_hdmf(d, freq, salary):
	amount = 0
	e_amount = 0
	ec = 0

	if freq == d['hdmf_freq'] or freq == 'Both':
		if d['hdmf_mode'] == "Manual":
			amount = flt(d['manual'], 2)

		elif d['hdmf_mode'] == "Table":
			table_amount = frappe.db.sql("""SELECT employee, employer FROM `tabHDMF Table` 
				WHERE %s >= beginning AND %s <= ending LIMIT 1 """,(salary, salary), as_dict=True )
			
			for t in table_amount:
				if t.employee:
					amount = t.employee
					e_amount = t.employer

		if d['hdmf_freq'] == 'Both':
			amount = amount / 2 
			e_amount = e_amount / 2

	return {
		"pay_desc": "HDMF",
		"pay_code": "HDMF",
		"amount": flt(amount, 2),
		"employer_amount": flt(e_amount, 2),
		"compensation": 0.0,
		"source": "Deduction",
		"account": "",
		"cost_center": "",
		"is_taxable": 0,
	}


def get_phic(d, freq, salary):
	amount = 0
	e_amount = 0
	ec = 0

	if freq == d['phic_freq'] or freq == 'Both':
		if d['phic_mode'] == "Manual":
			amount = flt(d['manual'], 2)

		elif d['phic_mode'] == "Percentage":	
			if salary < 10000 :
				amount = 137.50
				e_amount = 137.50
			elif salary > 39999.99:
				amount = 550.00
				e_amount = 550.00
			else:
				amount = (flt(salary, 2) * (flt(2.75,2) / 100) / 2)
				e_amount = (flt(salary, 2) * (flt(2.75,2) / 100) / 2)

		elif d['phic_mode'] == "Table":
			table_amount = frappe.db.sql("""SELECT employee FROM `tabPHIC Table` 
				WHERE %s >= beginning AND %s <= ending LIMIT 1 """,(salary, salary), as_dict=True )

			for t in table_amount:
				if t.employee:
					amount = t.employee

		if d['phic_freq'] == 'Both':
			amount = amount / 2
			e_amount = e_amount / 2

	return {
		"pay_desc": "PHIC",
		"pay_code": "PHIC",
		"amount": flt(amount, 2),
		"employer_amount": flt(e_amount, 2),
		"compensation": 0.0,
		"source": "Deduction",
		"account": "",
		"cost_center": "",
		"is_taxable": 0,
	}

def get_whtax(d, freq, salary):
	amount = 0
	if d['whtax_mode'] == "Manual":
		amount = flt(d['whtax_manual'], 2)
	
	elif d['whtax_mode'] == "Table":
		table_amount = frappe.db.sql("""SELECT compensatory, percentage FROM `tabTRAIN Table` 
			WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1 """,(salary, salary, d['payroll_schedule']), as_dict=True )

		if table_amount:
			for t in table_amount:
				amount = ( (salary) - t.compensatory) * (flt(t.percentage, 2) / 100) 

	if d['whtax_freq'] == 'Both':
		amount = amount / 2

	return amount

def get_attendance_deductions(employee, company, pay_from, pay_to, rate, no_hours):
	ot_amt = 0
	ot_mins = 0
	late_amt = 0
	late_mins = 0
	undertime_amt = 0
	undertime_mins = 0
	absent_amt = 0
	absent_mins = 0

	attendance = frappe.db.sql("""SELECT * FROM `tabAttendance Register` WHERE employee = %s AND target_date >= %s AND target_date <= %s""",(employee, pay_from, pay_to), as_dict=1)
	for at in attendance:
		if at.late > 0 and at.is_restday == 0 and at.is_absent != 1:
			late_mins += at.late
		elif at.is_absent == 1: 
			absent_mins += no_hours * 60

		if at.undertime > 0 and at.is_restday == 0:
			undertime_mins += at.undertime

		if at.is_absent == 1:
			ot_amt += 0
		else:
			ot_amt = at.overtime * rate

	late_amt = (late_mins ) * rate
	undertime_amt = (undertime_mins ) * rate
	absent_amt = (absent_mins ) * rate
	ot_amt = ot_amt 

	absent_register = {
		"pay_desc": "Absent",
		"pay_code": "Absent",
		"amount": flt(absent_amt, 2),
		"employer_amount": 0.0,
		"compensation": 0.0,
		"source": "Employee",
		"account": "",
		"cost_center": "",
		"is_taxable": 0,
	}

	ot_register = {
		"pay_desc": "Overtime",
		"pay_code": "Overtime",
		"amount": flt(ot_amt, 2),			
		"employer_amount": 0.0,
		"compensation": 0.0,
		"source": "Employee",
		"account": "",
		"cost_center": "",
		"is_taxable": 0,
	}

	late_register = {
		"pay_desc": "Late",
		"pay_code": "Late",
		"amount": flt(late_amt, 2),			
		"employer_amount": 0.0,
		"compensation": 0.0,
		"source": "Employee",
		"account": "",
		"cost_center": "",
		"is_taxable": 0,
	}

	ut_register = {
		"pay_code": "Undertime",
		"pay_desc": "Undertime",
		"amount": flt(undertime_amt, 2),
		"employer_amount": 0.0,
		"compensation": 0.0,
		"source": "Employee",
		"account": "",
		"cost_center": "",
		"is_taxable": 0,
	}

	return absent_register, late_register, ut_register, ot_register