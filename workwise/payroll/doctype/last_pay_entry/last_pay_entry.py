# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, hashlib
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, cstr
from frappe import _
from frappe.model.document import Document
from workwise.payroll.payroll_utils import get_rates
from workwise.payroll.annualization_utils import get_annual_results, get_annual_employees, get_annual_registers, get_annual_prev2316

class LastPayEntry(Document):
	def validate(self):
		self.get_totals()
		#self.get_register()

	def validate_entries(self):
		unique_list = []
		unique_entries = []
		for d in self.register_table:
			if not d.manually_encoded:
				auto_hash = cstr(d.transaction_type)+cstr(d.description)+cstr(d.type)+cstr(flt(d.amount, 2))+cstr(d.remarks)
				if auto_hash not in unique_list:
					unique_list.append(auto_hash)
					unique_entries.append({
						"transaction_type": d.transaction_type, "description": d.description, "type": d.type,
						"remarks": d.remarks, "amount": d.amount, "status": d.status, "manually_encoded": d.manually_encoded,
						"on_hold_pay": d.on_hold_pay,
					})
			else:
				manual_hash = cstr(d.description)+cstr(d.type)+cstr(d.amount)+cstr(d.remarks)
				if manual_hash not in unique_list:
					unique_list.append(manual_hash)
					unique_entries.append({
						"transaction_type": d.transaction_type, "description": d.description, "type": d.type,
						"remarks": d.remarks, "amount": d.amount, "status": d.status, "manually_encoded": d.manually_encoded,
						"on_hold_pay": d.on_hold_pay,
					});

		self.set('register_table', [])
		for ue in unique_entries:
			row = self.append('register_table', {})
			row.update(ue)

	def get_auto_entries(self):
		if self.docstatus == 1:
			frappe.throw(_("Lastpay Entry already submitted"))
		register = []
		entry=[]
		emp = frappe.db.sql("""SELECT * FROM tabEmployee WHERE `name` = %(employee)s LIMIT 1""",{ "employee": self.employee,}, as_dict=True)
		for r in self.get('register_table'):
			if r.manually_encoded:
				register.append({
					"transaction_type": r.transaction_type,
					"description": r.description,
					"type": r.type,
					"remarks": r.remarks,
					"amount": r.amount,
					"status": r.status,
					"manually_encoded": r.manually_encoded,
				})
		self.set('register', [])
		self.validate_dates()

		self.get_pro_rated(emp, register, entry)
		self.get_on_hold(emp, register, entry)
		self.get_leave_conversion(emp, register, entry)
		self.get_loan(emp ,register, entry)
		
		for d in register:
			row = self.append('register_table', {})
			row.update(d)
		self.validate_entries()
		return entry

	def validate_dates(self):
		from_year, to_year = frappe.db.get_value("Payroll Year", self.payroll_year, ["from_date", "to_date"])
		self.from_year = from_year
		self.to_year = to_year

		last_date_list = []
		date_hired, date_retired, date_resigned, date_terminated, date_contract_ended, last_date = None, None, None, None, None, None
		date_hired, date_retired, date_resigned, date_terminated, date_contract_ended = frappe.db.get_value("Employee", self.employee, ["date_hired", "date_retired", "date_resigned", "date_terminated", "date_contract_ended"])
		date_hired = getdate(date_hired)
		if date_retired:
			last_date_list.append(getdate(date_retired))
		if date_resigned:
			last_date_list.append(getdate(date_resigned))
		if date_terminated:
			last_date_list.append(getdate(date_terminated))
		if date_contract_ended:
			last_date_list.append(getdate(date_contract_ended))
		if last_date_list:
			last_date = max(last_date_list)
		if (date_hired) and (getdate(from_year) <= getdate(date_hired) <= getdate(to_year)) and (getdate(date_hired) > getdate(from_year)):
			self.from_year = date_hired
		if (last_date) and (getdate(from_year) <= getdate(last_date) <= getdate(to_year)) and (getdate(last_date) < getdate(to_year)):
			self.to_year = last_date

	def pre_annualization(self, tax_included_reg):
		pay_sched = frappe.db.get_value("Employee", self.employee, "payroll_schedule")
		from_year, to_year = frappe.db.get_value("Payroll Year", self.payroll_year, ["from_date", "to_date"])
		employees = get_annual_employees(self.employee, self.company, None, None, pay_sched, from_year, to_year)
		registers = get_annual_registers(self.employee, self.company, pay_sched, self.payroll_year, True)
		prev_2316 = get_annual_prev2316(self.employee, self.payroll_year)
		annual_registers = get_annual_results(employees, registers, prev_2316, tax_included_reg, self.payroll_year, from_year, to_year)
		for d in annual_registers:
			if d.employee == self.employee:
				self.prev_total_tax = d.prev_taxable_total
				self.pres_total_tax = d.taxable_total
				self.gross_taxable = (d.taxable_total + d.prev_taxable_total)
				self.tax_due = d.tax_due
				self.prev_tax_paid = d.prev_tax_withheld
				self.pres_tax_paid = d.tax_withheld + d.prev_tax_withheld
				self.tax_refund = d.adj_over_withheld
				self.deficit_tax = d.adj_amount_withheld
				self.excess_demi = d.excess_demi
				self.t_benefits = d.t_benefits
				if self.t_benefits < 0:
					self.t_benefits = 0
				self.nt_benefits = d.nt_benefits
				self.is_min_wage = d.minimum_wage

	def get_totals(self):
		tax_included_reg = []
		net_pay = 0.0
		for rt in self.register_table:
			tax_included_reg.append(frappe._dict({
				"employee": self.employee,
				"type": rt.type,
				"amount": flt(rt.amount, 2),
				"transaction_type": rt.transaction_type,
			}))
			if rt.type=="Income":
				net_pay+=flt(rt.amount, 2)
			elif rt.type=="Deduction":
				net_pay-=flt(rt.amount, 2)

		self.net_pay=net_pay
		self.pre_annualization(tax_included_reg)
		self.net_pay = self.net_pay + (self.tax_refund - abs(self.deficit_tax))

	def get_on_hold(self, employee ,register, entry):
		included_transactions = {}
		on_hold_registers = frappe.db.sql(""" SELECT PRE.pay_code, PRE.amount, TT.type, TT.title, PR.period, 
			PR.net_payroll, PR.gross_payroll, PRE.is_taxable, PRE.entry_type 
			FROM `tabPayroll Register Entries` PRE INNER JOIN `tabPayroll Register` PR ON PRE.`parent`=PR.`name` 
			INNER JOIN `tabTransaction Type` TT ON PRE.`pay_code`=TT.`name`
			INNER JOIN `tabPayroll Period` PP ON PR.`period`=PP.`name`
			WHERE PR.employee = %(employee)s AND PR.on_hold = 1 
			AND PP.payroll_year = %(payroll_year)s
			""",{
			"employee": self.employee,
			"payroll_year": self.payroll_year,
			"from_year": self.from_year,
			"to_year": self.to_year,
		}, as_dict=True)

		for d in on_hold_registers:
			if d.type in ['Income', 'Deduction'] and d.entry_type != 'Employer' :
				if d.pay_code not in included_transactions:
					included_transactions[d.pay_code] = {
						"amount": 0,
						"title": d.title,
						"type": d.type,
						"is_taxable": d.is_taxable,
					}
				included_transactions[d.pay_code]['amount'] += d.amount

		for inc in included_transactions:
			register.append({
				"transaction_type": inc,
				"description": included_transactions[inc]['title'],
				"type": included_transactions[inc]['type'],
				"remarks": "From on hold payroll",
				"on_hold_pay": 1,
				"amount": included_transactions[inc]['amount'],
				"manually_encoded": 0,
			})

	def get_pro_rated(self, employee ,register, entry):
		period_map = self.get_period_map()
		for emp in employee:
			present_days = 0
			total_bonus = 0
			remarks = ""
			rates = get_rates(emp)
			bonus_method = frappe.db.get_single_value("Payroll Settings", "bonus_method")
			if bonus_method == "Standard":
				registerx = frappe.db.sql(""" SELECT PRE.`name`, PRE.`pay_code`, PRE.`amount`
					FROM `tabPayroll Register Entries` PRE 
					INNER JOIN `tabPayroll Register` PR ON PRE.`parent`=PR.`name`
					INNER JOIN `tabPayroll Period` PP ON PR.`period`=PP.`name`
					WHERE PRE.`pay_code` = 'BS' AND PR.`employee` = %(employee)s 
					AND PP.payroll_year = %(payroll_year)s
					#AND ((from_year)s BETWEEN PP.attendance_from AND PP.attendance_to
					#	OR (to_year)s BETWEEN PP.attendance_from AND PP.attendance_to
					#	OR PP.attendance_from BETWEEN (from_year)s AND (to_year)s
					#	OR PP.attendance_to BETWEEN (from_year)s AND (to_year)s)
					""",{ 
					"employee": self.employee,
					"payroll_year": self.payroll_year,
					"from_year": self.from_year,
					"to_year": self.to_year,
				}, as_dict=True)

				for d in registerx:
					if d.pay_code == 'BS':
						total_bonus += d.amount

				remarks = "( "+ str(total_bonus) +" / 12 " + ")"
				total_bonus_basis = total_bonus
				total_bonus = total_bonus / 12

			if bonus_method == "Bonus Basis":
				bonus_basis = frappe.db.sql(""" SELECT PR.bonus FROM `tabPayroll Register` PR
					INNER JOIN `tabPayroll Period` PP ON PR.`period`=PP.`name` 
					WHERE PR.employee = %(employee)s 
					AND PP.payroll_year = %(payroll_year)s
					#AND ((from_year)s BETWEEN PP.attendance_from AND PP.attendance_to
					#	OR (to_year)s BETWEEN PP.attendance_from AND PP.attendance_to
					#	OR PP.attendance_from BETWEEN (from_year)s AND (to_year)s
					#	OR PP.attendance_to BETWEEN (from_year)s AND (to_year)s)
					""",{ 
					"employee": self.employee,
					"payroll_year": self.payroll_year,
					"from_year": self.from_year,
					"to_year": self.to_year,
				}, as_dict=True)

				for d in bonus_basis:
					total_bonus += d.bonus

				remarks = "( "+ str(total_bonus) +" / 12 " + ")"
				total_bonus_basis = total_bonus
				total_bonus = total_bonus / 12

			if bonus_method == "Attendance Base":
				att = frappe.db.sql(""" SELECT PRE.`name`, PRE.`pay_code`, PRE.`amount`, TT.`entry_type`, TT.`type` 
					FROM `tabPayroll Register Entries` PRE 
					INNER JOIN `tabPayroll Register` PR ON PRE.`parent`=PR.`name`
					INNER JOIN `tabTransaction Type` TT ON PRE.`pay_code`=TT.`name` 
					INNER JOIN `tabPayroll Period` PP ON PR.`period`=PP.`name`
					WHERE PR.`employee` = %(employee)s 
					AND PP.payroll_year = %(payroll_year)s
					#AND ((from_year)s BETWEEN PP.attendance_from AND PP.attendance_to
					#	OR (to_year)s BETWEEN PP.attendance_from AND PP.attendance_to
					#	OR PP.attendance_from BETWEEN (from_year)s AND (to_year)s
					#	OR PP.attendance_to BETWEEN (from_year)s AND (to_year)s)
					""",{ 
					"employee": self.employee,
					"payroll_year": self.payroll_year,
					"from_year": self.from_year,
					"to_year": self.to_year,
				}, as_dict=True)

				for d in att:
					if d.pay_code == 'BS':
						total_bonus += d.amount

					if d.entry_type == 'Attendance':
						if d.type == 'Income':
							total_bonus += d.amount
						if d.type == 'Deduction':
							total_bonus -= d.amount

				remarks = "( "+ str(total_bonus) +" / 12 " + ")"
				total_bonus_basis = total_bonus
				total_bonus = total_bonus / 12

			#ceiling_bonus = frappe.db.get_single_value("Payroll Settings", "ceiling_month_pay")
			#if ceiling_bonus:
			#	if flt(total_bonus) > flt(ceiling_bonus):
			#		total_bonus = flt(ceiling_bonus)
			#	else:
			#		total_bonus = flt(total_bonus)

			register.append({
				"transaction_type": "PR13th_Month",
				"description": "Pro Rated 13th Month",
				"type": "Income",
				"remarks": remarks,
				"amount": total_bonus,
				"manually_encoded": 0,
			})
			#entry["total_bonus_basis"] += total_bonus_basis
			#entry["net_pay"] += total_bonus

	def get_loan(self, employee ,register, entry):
		unpaid_loans = {}
		paid_loans = {}
		total_unpaid = 0
		total_paid = 0
		loans = frappe.db.sql(""" SELECT LA.`name`, LA.`unpaid_amount`, LA.`loan_type`, LA.`loan_name`, LA.`paid_amount`
		 FROM `tabLoan Application` LA INNER JOIN `tabTransaction Type` TT ON LA.`loan_type`=TT.`name`
		WHERE LA.`employee` = %(employee)s AND LA.`docstatus` = 1 AND (TT.`is_gov_loan` = 0 OR TT.`name` = 'ES') """,{ 
			"employee": self.employee,
		}, as_dict=True)

		for d in loans:
			if d.unpaid_amount > 0:
				if d.loan_type != "ES":
					if d.loan_type not in unpaid_loans:
						unpaid_loans[d.loan_type] = {
							"transaction_type": d.loan_type,
							"description": "Unpaid Loans",
							"type": "Deduction",
							"remarks": ""+str(d.loan_name)+"",
							"amount": 0,
							"manually_encoded": 0,
						}
						unpaid_loans[d.loan_type]['amount'] += d.unpaid_amount
						total_unpaid += d.unpaid_amount
						
			if d.paid_amount > 0:
				if d.loan_type == "ES":
					if d.loan_type not in paid_loans:
						paid_loans[d.loan_type] = {
							"transaction_type": "ES",
							"description": "Employee Savings",
							"type": "Income",
							"remarks": ""+str(d.loan_name)+"",
							"amount": 0,
							"manually_encoded": 0,
						}
					paid_loans[d.loan_type]['amount'] += d.paid_amount
					total_unpaid += d.paid_amount

		for unp in unpaid_loans:
			register.append({
				"transaction_type": unpaid_loans[unp]['transaction_type'],
				"description": unpaid_loans[unp]['description'],
				"type": unpaid_loans[unp]['type'],
				"remarks": unpaid_loans[unp]['remarks'],
				"amount": unpaid_loans[unp]['amount'],
				"manually_encoded": 0,
			})

		for pd in paid_loans:
			register.append({
				"transaction_type": paid_loans[pd]['transaction_type'],
				"description": paid_loans[pd]['description'],
				"type": paid_loans[pd]['type'],
				"remarks": paid_loans[pd]['remarks'],
				"amount": paid_loans[pd]['amount'],
				"manually_encoded": 0,
			})


		#entry["net_pay"] -= total_unpaid
		#entry["net_pay"] += total_paid

	def get_period_map(self):
		period_map = {}
		period = frappe.db.sql(""" SELECT name, payroll_year FROM `tabPayroll Period` WHERE payroll_year = %s """, self.payroll_year, as_dict=True)
		for pr in period:
			period_map[pr.name] = {
				"payroll_year": pr.payroll_year,
				"name": pr.name,
			}
		return period_map

	def get_leave_conversion(self, employee, register, entry):
		for emp in employee:
			rates = get_rates(emp)
			convertible_leaves = frappe.db.sql(""" SELECT `name`, leave_name, leave_code FROM `tabLeave Type` WHERE convertible = 1 """, as_dict=True)
			for lv in convertible_leaves:
				total_amt = 0
				valid_entry = {}
				less_entry = {}
				total_balance = 0
				lb_entries = frappe.db.sql(""" SELECT * FROM `tabLB Entry` WHERE `employee` = %s AND (`leave_type` = %s OR `deduct_credits_to` = %s) ORDER BY `from_date` ASC """, (emp.name, lv.name, lv.name), as_dict=1)
				for d in lb_entries:
					if d.balance_type == "Add":
						if lv.name == d.leave_type:
							if d.name not in valid_entry:
								valid_entry[d.name] = {
									"credits": d.credits,
									"from": getdate(d.from_date),
									"to": getdate(d.to_date),
								}
					else:
						if d.deduct_credits_to == lv.name:
							if d.name not in less_entry:
								less_entry[d.name] = {
									"used": 0,
									"credits": d.credits,
									"from": getdate(d.from_date),
									"to": getdate(d.to_date),
								}

				for vl in valid_entry:
					to_less = 0
					for le in less_entry:
						if valid_entry[vl]['credits'] > 0 and not less_entry[le]['used']:
							if ( valid_entry[vl]['from'] <= less_entry[le]['from'] <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= less_entry[le]['to'] <= valid_entry[vl]['to'] ):
								to_less += less_entry[le]['credits']
								less_entry[le]['used'] = 1
					valid_entry[vl]['credits'] -= to_less
					if (( valid_entry[vl]['from'] <= getdate(self.from_year) <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= getdate(self.to_year) <= valid_entry[vl]['to'] ))\
					or (( getdate(self.from_year) <= valid_entry[vl]['from'] <= getdate(self.to_year) ) or ( getdate(self.from_year) <= valid_entry[vl]['to'] <= getdate(self.to_year) )):
						total_balance += valid_entry[vl]['credits']
				
				if total_balance <= 0:
					total_balance = 0

				total_amt += rates.get('daily_rate') * (total_balance)
				if total_amt:
					register.append({
						"transaction_type": "LC",
						"description": "Convertible "+ str(d.leave_type) +"", 
						"type": "Income",
						"remarks": ""+ str( flt(rates.get('daily_rate'), 8) ) +" x "+ str(total_balance)+" Credit/s",
						"amount": total_amt,
						"manually_encoded": 0,
					})

				#entry["pres_total_tax"] += total_amt
				#entry["net_pay"] += total_amt

	def clear_entries(self):
		self.net_pay = 0
		self.prev_total_tax = 0
		self.pres_total_tax = 0
		self.gross_taxable = 0
		self.tax_due = 0
		self.prev_tax_paid = 0
		self.pres_tax_paid = 0
		self.deficit_tax = 0
		self.tax_refund = 0