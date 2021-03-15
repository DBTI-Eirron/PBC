# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, cstr
from frappe import _
from frappe.model.document import Document
from workwise.payroll.payroll_utils import get_rates
get_annual_employees

class LastPayEntry(Document):
	def validate(self):
		self.get_register()

	def validate_entries(self):
		unique_ent = []
		unique_entries = []

		for d in self.register_table:
			if not d.manually_encoded:
				if cstr(d.transaction_type)+cstr(d.description)+cstr(d.type)+cstr(flt(d.amount, 2))+cstr(d.remarks) not in unique_ent:
					unique_ent.append( cstr(d.transaction_type)+cstr(d.description)+cstr(d.type)+cstr(flt(d.amount, 2))+cstr(d.remarks) );

					i = {
						"transaction_type": d.transaction_type,
						"description": d.description,
						"type": d.type,
						"remarks": d.remarks,
						"amount": d.amount,
						"status": d.status,
						"manually_encoded": d.manually_encoded,
					}
					unique_entries.append(i);
			else:
				if cstr(d.description)+cstr(d.type)+cstr(d.amount)+cstr(d.remarks) not in unique_ent:
					unique_ent.append(cstr(d.description)+cstr(d.type)+cstr(d.amount)+cstr(d.remarks));

					j = {
						"transaction_type": d.transaction_type,
						"description": d.description,
						"type": d.type,
						"remarks": d.remarks,
						"amount": d.amount,
						"status": d.status,
						"manually_encoded": d.manually_encoded,
					}
					unique_entries.append(j);

		self.set('register_table', [])
		for ue in unique_entries:
			row = self.append('register_table', {})
			row.update(ue)

	def get_register(self):
		register = []
		tax_included_reg = []
		entry = {
			"13th_month": 0,
			"net_pay": 0,
			"prev_total_tax": 0,
			"pres_total_tax": 0,
			"gross_taxable": 0,
			"tax_due": 0,
			"prev_tax_paid": 0,
			"pres_tax_paid": 0,
			"not_yet_paid": 0,
			"total_bonus_basis": 0,
		}

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

		#self.get_pro_rated_taxable(emp, register, entry)
		self.pre_annualization(entry, tax_included_reg)
		
		for d in register:
			row = self.append('register_table', {})
			row.update(d)
		self.validate_entries()
		self.compute_summary(emp, register, entry)
		self.set_summary(entry)

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

	def pre_annualization(self, entry, tax_included_reg):
		pay_sched = frappe.db.get_value("Payroll Year", self.employee, "payroll_schedule")
		from_year, to_year = frappe.db.get_value("Payroll Year", self.payroll_year, ["from_date", "to_date"])
		employees = get_annual_employees(self.employee, None, None, None, pay_sched, from_year, to_year)
		registers = get_annual_registers(self.employee, self.company, self.payroll_schedule, self.payroll_year, False)
		prev_2316 = get_annual_prev2316(self.employee, self.payroll_year)
		annual_registers = get_annual_entries(employees, registers, prev_2316, tax_included_reg, self.payroll_year, from_year, to_year)

		for d in annual_registers:
			if d.employee == self.employee:
				["prev_total_tax"] = d.prev_taxable_total
				["pres_total_tax"] = d.taxable_total
				["gross_taxable"] = (d.taxable_total + d.taxable_total)
				["tax_due"] = d.tax_due
				["prev_tax_paid"] = d.prev_tax_withheld
				["pres_tax_paid"] = d.tax_withheld
				["tax_refund"] = 0.0
				["deficit_tax"] = 0.0

	def get_on_hold(self, employee ,register, entry):
		included_transactions = {}
		total_bonus = 0
		net_payroll = 0.0
		pres_total_tax = 0.0
		bonus = frappe.db.sql(""" SELECT PRE.pay_code, PRE.amount, TT.type, TT.title, PR.period, 
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

		for d in bonus:
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
				"type": "Add" if included_transactions[inc]['type'] == 'Income' else "Less",
				"remarks": "On Hold Payroll",
				"amount": included_transactions[inc]['amount'],
				"manually_encoded": 0,
			})

		return register

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

			ceiling_bonus = frappe.db.get_single_value("Payroll Settings", "ceiling_month_pay")
			if ceiling_bonus:
				if flt(total_bonus) > flt(ceiling_bonus):
					total_bonus = flt(ceiling_bonus)
				else:
					total_bonus = flt(total_bonus)

			register.append({
				"transaction_type": "PR13th_Month",
				"description": "Pro Rated 13th Month",
				"type": "Add",
				"remarks": remarks,
				"amount": total_bonus,
				"manually_encoded": 0,
			})

			tax_included_reg.append({
				"employee": self.get_employee,
				"_type": "Income",
				"amount": total_bonus,
				"transaction_type": "PR13th_Month",
			})			

			entry["total_bonus_basis"] += total_bonus_basis
			entry["net_pay"] += total_bonus

	def get_pro_rated_taxable(self, employee ,register, entry):
		ceiling_bonus = frappe.db.get_single_value("Payroll Settings", "ceiling_month_pay")
		if ceiling_bonus:
			total_bonus = 0
			if flt(entry["total_bonus_basis"]) > flt(ceiling_bonus):
				total_bonus = (flt(entry["total_bonus_basis"]) / 12) - flt(ceiling_bonus)
				remarks = "( "+ str(entry["total_bonus_basis"]) + " / 12 ) "+" - "+str(ceiling_bonus)+")"

			if total_bonus > 0:
				register.append({
					"transaction_type": "PRT13th_Month",
					"description": "Pro Rated Taxable 13th Month",
					"type": "Add",
					"remarks": remarks,
					"amount": total_bonus,
					"manually_encoded": 0,
				})

		return register

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
							"type": "Less",
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
							"type": "Add",
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


		entry["net_pay"] -= total_unpaid
		entry["net_pay"] += total_paid

		return register

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
						"type": "Add",
						"remarks": ""+ str( flt(rates.get('daily_rate'), 8) ) +" x "+ str(total_balance)+" Credit/s",
						"amount": total_amt,
						"manually_encoded": 0,
					})

					tax_included_reg.append({
						"employee": self.get_employee,
						"_type": "Income",
						"amount": total_amt,
						"transaction_type": "LC",
					})	

				#entry["pres_total_tax"] += total_amt
				entry["net_pay"] += total_amt

		return registers

	def compute_summary(self, employee, register, entry):
		entry["gross_taxable"] = entry["prev_total_tax"] + entry["pres_total_tax"]

		tax_due = 0.0
		train_compensatory = 0.0
		train_prescribed = 0.0
		train_percentage = 0.0
		for emp in employee:
			rates = get_rates(emp)
			bracket = frappe.db.sql(""" SELECT DISTINCT `compensatory`, `prescribed`, `percentage` FROM `tabTRAIN Table` WHERE `frequency` = "Yearly" AND %(amount)s BETWEEN `beginning` AND `ending` LIMIT 1 """,{
				"amount": entry["gross_taxable"],
			}, as_dict=True)

			if bracket:
				for d in bracket:
					train_compensatory = d.compensatory
					train_prescribed = d.prescribed
					train_percentage = d.percentage

		tax_due = entry["gross_taxable"] - train_compensatory 
		tax_due = tax_due * (train_percentage / 100)
		tax_due = tax_due + train_prescribed

		entry["tax_due"] += tax_due

		if entry["tax_due"] > 0:
			entry["not_yet_paid"] = entry["tax_due"] - entry["pres_tax_paid"] - entry["prev_tax_paid"]
		else:
			entry["not_yet_paid"] = entry["tax_due"] - entry["pres_tax_paid"] 

	def set_summary(self, entry):
		self.clear_entries()
		total_add, total_less = 0, 0
		for d in self.register_table:
			if d.type == "Add":
				total_add += d.amount
			elif d.type == "Less":
				total_less += d.amount
		
		self.net_pay = flt(total_add, 8) - flt(total_less, 8) - flt(entry["not_yet_paid"], 8)
		self.prev_total_tax = flt(entry["prev_total_tax"], 8)
		self.pres_total_tax = flt(entry["pres_total_tax"], 8)
		self.gross_taxable = flt(entry["gross_taxable"], 8)
		self.tax_due = flt(entry["tax_due"], 8)
		self.prev_tax_paid = flt(entry["prev_tax_paid"], 8)
		self.pres_tax_paid = flt(entry["pres_tax_paid"], 8)
		if flt(entry["not_yet_paid"], 8) > 0:
			self.deficit_tax = abs(flt(entry["not_yet_paid"], 8))
		else:
			self.tax_refund = abs(flt(entry["not_yet_paid"], 8))

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