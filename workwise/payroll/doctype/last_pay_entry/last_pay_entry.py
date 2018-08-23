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

	def get_pro_rated(self, employee ,register):
		for d in employee:
			start_date = d.date_hired
			if d.date_retired:
				end_date = d.date_retired
			elif d.date_terminated:
				end_date = d.date_terminated
			elif d.date_resigned:
				end_date = d.date_resigned

		total_bonus = 0
		bonus = frappe.db.sql(""" SELECT bonus FROM `tabPayroll Register` WHERE employee = %(employee)s AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s """,{ 
			"employee": self.employee,
			"from_year": self.from_year,
			"to_year": self.to_year,
		}, as_dict=True)

		cutoff = 0
		for d in bonus:
			total_bonus += d.bonus
			cutoff += 1

		total_bonus = total_bonus / cutoff

		register.append({
			"description": "Pro Rated 13th Month",
			"type": "Add",
			"remarks": "",
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
							"remarks": ""+ str( flt(rates.get('daily_rate'), 2) ) +" x "+ str(credits)+" Credit/s",
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