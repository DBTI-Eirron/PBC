# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document

class LastPayEntry(Document):
	def get_register(self):
		emp = frappe.db.sql("""SELECT * FROM tabEmployee WHERE `name` = %(employee)s LIMIT 1""",{ "employee": self.employee,}, as_dict=True)
		self.set('register', [])
		register = []

		self.get_on_hold(emp, register)	
		self.get_pro_rated(emp, register)
		self.get_leave_conversion(emp, register)
		self.get_loan(emp ,register)
		for d in register:
			row = self.append('register', {})
			row.update(d)

		total_add, total_less = 0, 0
		for d in self.register:
			if d.type == "Add":
				total_add += d.amount
			elif d.type == "Less":
				total_less += d.amount


		self.total_pay = total_add - total_less 

	def get_on_hold(self, employee ,register):
		total_bonus = 0

		bonus = frappe.db.sql(""" SELECT period, net_payroll FROM `tabPayroll Register` WHERE employee = %(employee)s 
			AND on_hold = 1 AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s """,{ 
			"employee": self.employee,
			"from_year": self.from_year,
			"to_year": self.to_year,
		}, as_dict=True)

		for d in bonus:
			register.append({
				"description": "On Hold Payroll",
				"type": "Add",
				"remarks": ""+str(d.period)+"",
				"amount": d.net_payroll,
			})

		return register

	def get_pro_rated(self, employee ,register):
		for emp in employee:
			present_days = 0
			total_bonus = 0
			remarks = ""
			rates = self.get_rates(emp)
			bonus_method = frappe.db.get_single_value("Payroll Settings", "bonus_method")

			if bonus_method == "Standard":
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
						total_rate = d.monthly_rate
					if d.schedule == "Monthly":
						months += 1
						total_rate = d.monthly_rate

				total_bonus += total_rate * months / 12
				remarks = "( "+ str(total_rate) +" x "+ str(months)+" / 12 "+ ")"

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
					if d.schedule == "Monthly":
						months += 1
						total_rate += d.bonus

				total_bonus += total_rate / months
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

		return register

	def get_loan(self, employee ,register):
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

		return register

	def get_leave_conversion(self, employee, register):
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