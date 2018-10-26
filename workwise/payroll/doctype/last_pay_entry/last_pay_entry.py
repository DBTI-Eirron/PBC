# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document

class LastPayEntry(Document):
	def validate(self):
		self.get_register()

	def get_register(self):
		entry = {
			"net_pay": 0.0,
			"prev_total_tax": 0.0,
			"pres_total_tax": 0.0,
			"gross_taxable": 0.0,
			"tax_due": 0.0,
			"prev_tax_paid": 0.0,
			"pres_tax_paid": 0.0,
			"not_yet_paid": 0.0,
		}

		emp = frappe.db.sql("""SELECT * FROM tabEmployee WHERE `name` = %(employee)s LIMIT 1""",{ "employee": self.employee,}, as_dict=True)
		self.set('register', [])
		register = []

		self.get_on_hold(emp, register, entry)
		self.get_register_entries(emp, register, entry)
		self.get_pro_rated(emp, register, entry)
		self.get_leave_conversion(emp, register, entry)
		self.get_loan(emp ,register, entry)
		self.get_previous_bir(emp, register, entry)
		self.get_paid_payroll(emp, register, entry)
		self.get_present_tax_paid(emp, register, entry)
		for d in register:
			row = self.append('register', {})
			row.update(d)
		self.compute_summary(emp, register, entry)
		self.set_summary(entry)

	def get_on_hold(self, employee ,register, entry):
		total_bonus = 0
		net_payroll = 0.0
		pres_total_tax = 0.0
		bonus = frappe.db.sql(""" SELECT period, net_payroll, gross_payroll FROM `tabPayroll Register` WHERE employee = %(employee)s 
			AND on_hold = 1 AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s """,{ 
			"employee": self.employee,
			"from_year": self.from_year,
			"to_year": self.to_year,
		}, as_dict=True)

		for d in bonus:
			net_payroll += d.gross_payroll
			pres_total_tax += d.gross_payroll
			register.append({
				"description": "On Hold Payroll",
				"type": "Add",
				"remarks": ""+str(d.period)+"",
				"amount": d.gross_payroll,
			})

		entry["net_pay"] += net_payroll
		entry["gross_taxable"] += pres_total_tax
		entry["pres_total_tax"] += pres_total_tax

		return register

	def get_register_entries(self, employee ,register, entry):
		other_deductions = 0
		payreg = frappe.db.sql(""" SELECT PR.period, PR.net_payroll, PR.gross_payroll, PRE.amount, PRE.pay_type, PRE.entry_type FROM `tabPayroll Register` PR 
			INNER JOIN `tabPayroll Register Entries` PRE ON PRE.parent = PR.`name`
			WHERE PR.employee = %(employee)s AND PR.on_hold = 1 AND PR.posting_date >= %(from_year)s AND PR.posting_date <= %(to_year)s """,{ 
				"employee": self.employee,
				"from_year": self.from_year,
				"to_year": self.to_year,
		}, as_dict=True)

		for d in payreg:
			if d.pay_type == "Deduction" and d.entry_type == "Other":
				other_deductions += d.amount

		if other_deductions > 0:
			register.append({
				"description": "Other Deductions",
				"type": "Less",
				"remarks": "",
				"amount": other_deductions,
			})
	
		entry["net_pay"] -= other_deductions
	
		return register

	def get_paid_payroll(self, employee ,register, entry):
		pres_total_tax = 0.0
		paid_payroll = frappe.db.sql(""" SELECT period, net_payroll, gross_payroll FROM `tabPayroll Register` WHERE employee = %(employee)s 
			AND on_hold = 0 AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s """,{ 
			"employee": self.employee,
			"from_year": self.from_year,
			"to_year": self.to_year,
		}, as_dict=True)

		for d in paid_payroll:
			pres_total_tax += d.gross_payroll

		entry["pres_total_tax"] += pres_total_tax

	def get_pro_rated(self, employee ,register, entry):
		for emp in employee:
			present_days = 0
			total_bonus = 0
			remarks = ""
			rates = self.get_rates(emp)
			bonus_method = frappe.db.get_single_value("Payroll Settings", "bonus_method")

			if bonus_method == "Standard":
				registerx = frappe.db.sql(""" SELECT schedule, bonus, monthly_rate FROM `tabPayroll Register` WHERE employee = %(employee)s 
					AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s AND schedule = %(schedule)s """,{ 
					"employee": self.employee,
					"from_year": self.from_year,
					"to_year": self.to_year,
					"schedule": emp.payroll_schedule,
				}, as_dict=True)

				total_rate = 0.0
				months = 0.0
				for d in registerx:
					if d.schedule == "Semi-Monthly":
						months += 0.5
						total_rate = d.monthly_rate
					if d.schedule == "Monthly":
						months += 1
						total_rate = d.monthly_rate

				total_bonus += total_rate * months / 12
				remarks = "( "+ str(total_rate) +" x "+ str(months)+" / 12 " + ")"

			if bonus_method == "Bonus Basis":
				register = frappe.db.sql(""" SELECT schedule, bonus FROM `tabPayroll Register` WHERE employee = %(employee)s 
					AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s AND schedule = %(schedule)s """,{ 
					"employee": self.employee,
					"from_year": self.from_year,
					"to_year": self.to_year,
					"schedule": emp.payroll_schedule,
				}, as_dict=True)

				total_rate = 0.0
				months = 0.0
				for d in register:
					if d.schedule == "Semi-Monthly":
						months += 0.5
						total_rate += d.bonus
					elif d.schedule == "Monthly":
						months += 1
						total_rate += d.bonus

				total_bonus += total_rate / 12
				remarks = "( "+ str(total_rate) +" / "+ str(months)+" )"

			if bonus_method == "Attendance Base":
				att = frappe.db.sql(""" SELECT bonus, present_days FROM `tabPayroll Register` WHERE employee = %(employee)s AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s """,{ 
					"employee": self.employee,
					"from_year": self.from_year,
					"to_year": self.to_year,
				}, as_dict=True)
				present_days = 0
				for d in att:
					present_days += d.present_days

				total_bonus = ( present_days / emp.get('total_yr_days')) * flt(rates.get('monthly_rate'), 8)
				remarks = "("+ str(present_days) +" / "+ str(emp.get('total_yr_days'))+") x "+ str(flt(rates.get('monthly_rate'), 8)) +""

			register.append({
				"description": "Pro Rated 13th Month",
				"type": "Add",
				"remarks": remarks,
				"amount": total_bonus,
			})


			entry["pres_total_tax"] += total_bonus
			entry["gross_taxable"] += total_bonus
			entry["net_pay"] += total_bonus

		return register

	def get_loan(self, employee ,register, entry):
		total = 0
		loans = frappe.db.sql(""" SELECT * FROM `tabLoan Application` WHERE employee = %(employee)s """,{ 
			"employee": self.employee,
		}, as_dict=True)

		for d in loans:
			total += d.unpaid_amount
			register.append({
				"description": "Unpaid Loans",
				"type": "Less",
				"remarks": ""+str(d.loan_name)+"",
				"amount": total,
			})

		entry["pres_total_tax"] -= total
		entry["net_pay"] -= total

		return register

	def get_leave_conversion(self, employee, register, entry):
		for emp in employee:
			rates = self.get_rates(emp)
			convertible_leaves = frappe.db.sql(""" SELECT leave_name, leave_code FROM `tabLeave Type` WHERE convertible = 1 """, as_dict=True)
			for d in convertible_leaves:
				total_amt = 0
				balances = frappe.db.sql("""SELECT * FROM `tabLeave Balance` WHERE employee = %(employee)s AND leave_type = %(leave_type)s """,{ 
					"employee": self.employee,
					"leave_type": d.leave_name,
				}, as_dict=True)
				for b in balances:
					credits = (b.credits - b.used_credits)
					total_amt += rates.get('daily_rate') * (credits)
					if total_amt:
						register.append({
							"description": "Convertible "+ str(b.leave_type) +"", 
							"type": "Add",
							"remarks": ""+ str( flt(rates.get('daily_rate'), 8) ) +" x "+ str(credits)+" Credit/s",
							"amount": total_amt,
						})

				entry["pres_total_tax"] += total_amt
				entry["net_pay"] += total_amt

		return register

	def get_rates(self, emp):
		monthly_rate = 0.0
		hourly_rate = 0.0
		semi_rate = 0.0
		daily_rate = 0.0
		if emp['rate'] > 0 and  emp['total_yr_days'] > 0 and emp['no_hours'] > 0:
			month_days = (flt(emp['total_yr_days'], 8) / 12)
			if emp['rate_type'] == "Monthly Rate":
				monthly_rate = flt(emp['rate'], 8)
				semi_rate = flt(emp['rate'], 8) / 2
				daily_rate = flt(emp['rate'], 8) / month_days
				hourly_rate = ( flt(emp['rate'], 8) / month_days ) / emp['no_hours']

			elif emp['rate_type'] == "Hourly Rate":
				monthly_rate = ( flt(emp['rate'], 8) * emp['no_hours'] ) * month_days
				semi_rate = ( flt(emp['rate'], 8) * emp['no_hours'] ) * (month_days / 2)
				daily_rate = flt(emp['rate'], 8) * emp['no_hours']
				hourly_rate = flt(emp['rate'], 8)

			elif emp['rate_type'] == "Daily Rate":
				monthly_rate = flt(emp['rate'], 8) * month_days
				semi_rate = flt(emp['rate'], 8) * (month_days / 2)
				daily_rate = flt(emp['rate'], 8)
				hourly_rate = flt(emp['rate'], 8) / emp['no_hours']

		return {
			"monthly_rate": monthly_rate,
			"semi_rate": semi_rate,
			"daily_rate": daily_rate,
			"hourly_rate": flt(hourly_rate, 8)
		}

	def get_previous_bir(self, employee, register, entry):
		prev_tax_paid = 0.0
		prev_total_tax = 0.0
		prev_bir = frappe.db.sql(""" SELECT DISTINCT `name`, tax_bs+tax_bonus as total_taxable, sum_atw_prev as tax_paid FROM `tabBIR2316` WHERE `docstatus` = 1 AND `document_type` = "Previous" AND `employee` = %(employee)s  AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s  """,{ 
			"employee": self.employee,
			"from_year": self.from_year,
			"to_year": self.to_year,
		}, as_dict=True)

		if prev_bir:
			for d in prev_bir:
				if d.name:
					prev_tax_paid += d.tax_paid
					prev_total_tax += d.total_taxable
					register.append({
						"description": "Previous BIR 2316",
						"type": "Add",
						"remarks": ""+str(d.name)+"",
						"amount": d.total_taxable,
					})
				else:
					break;

		entry["prev_tax_paid"] += prev_tax_paid
		entry["prev_total_tax"] += prev_total_tax

		return register

	def get_present_tax_paid(self, employee, register, entry):
		pres_tax_paid = 0.0
		pres_tax = frappe.db.sql(""" SELECT PE.`amount` FROM `tabPayroll Register Entries` PE JOIN `tabPayroll Register` PR ON PE.`parent` = PR.`name` WHERE PE.`pay_code` = "WHTAX" AND PR.on_hold = 0 AND PR.posting_date >= %(from_year)s AND PR.posting_date <= %(to_year)s AND PR.employee = %(employee)s  """,{ 
			"employee": self.employee,
			"from_year": self.from_year,
			"to_year": self.to_year,
		}, as_dict=True)

		if pres_tax:
			for d in pres_tax:
				if d.amount:
					pres_tax_paid += d.amount
				else:
					break;

		entry["pres_tax_paid"] += pres_tax_paid

		return register

	def compute_summary(self, employee, register, entry):
		total_add, total_less = 0, 0
		for d in self.register:
			if d.type == "Add":
				total_add += d.amount
			elif d.type == "Less":
				total_less += d.amount

		entry["gross_taxable"] = entry["prev_total_tax"] + entry["pres_total_tax"]

		tax_due = 0.0
		train_compensatory = 0.0
		train_prescribed = 0.0
		train_percentage = 0.0
		for emp in employee:
			rates = self.get_rates(emp)
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
		self.net_pay = flt(entry["net_pay"], 8) - flt(entry["not_yet_paid"], 8)
		self.prev_total_tax = flt(entry["prev_total_tax"], 8)
		self.pres_total_tax = flt(entry["pres_total_tax"], 8)
		self.gross_taxable = flt(entry["gross_taxable"], 8)
		self.tax_due = flt(entry["tax_due"], 8)
		self.prev_tax_paid = flt(entry["prev_tax_paid"], 8)
		self.pres_tax_paid = flt(entry["pres_tax_paid"], 8)
		self.not_yet_paid = flt(entry["not_yet_paid"], 8)