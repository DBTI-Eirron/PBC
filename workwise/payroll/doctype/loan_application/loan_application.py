# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, cstr, nowdate
from frappe.model.document import Document

class LoanApplication(Document):
	def validate(self):
		self.update_missing_names()
		self.update_amounts()
		self.update_paid_unpaid()
		self.validate_date()
		self.validate_user_sensitivity_level()

	def update_missing_names(self):
		self.employee_name = frappe.db.get_value("Employee", self.employee, "full_name")
		self.loan_name = frappe.db.get_value("Transaction Type", self.loan_type, "title")

	def validate_date(self):
		if self.release_date > self.payment_start:
			frappe.throw(("Release Date should not be greater than Payment Start")) 

	def update_amounts(self):
		if self.loan_amount and self.amortization:
			multiplier = 2 if self.payment_frequency == 'Both' else 1

			total_loan =  self.loan_amount + (self.loan_amount * (flt(self.interest,2) / 100)) if self.interest > 0 else self.loan_amount
			self.total_loan = total_loan

			unpaid_amount = total_loan - self.beginning_balance if self.beginning_balance > 0 else total_loan

			entries = []
			self.set('payments', [])
			if self.beginning_balance >= total_loan:
				frappe.throw(("Beginning Balance should not be greater than Total Loan")) 
				
			total_payables = unpaid_amount
			if self.beginning_balance:
				entries.append({
					"payment_amount": self.beginning_balance,
					"payment_status": "Paid",
					"payment_date": self.posting_date,
				});

			while total_payables > 0:
				pay_amount = self.amortization / multiplier
				if not total_payables >= pay_amount:
					pay_amount = total_payables

				info = {"payment_amount": pay_amount, "payment_status": "Unpaid", "payment_date": None}

				total_payables -= pay_amount
				entries.append(info);

			for d in entries:
				row = self.append('payments', {})
				row.update(d)
		else:
			frappe.throw(("Loan Amount and No of Payments is Required"))

	def update_paid_unpaid(self):
		total_paid, total_unpaid = 0, 0
		for d in self.payments:
			if d.payment_status == 'Paid':
				total_paid += d.payment_amount
			else:
				total_unpaid += d.payment_amount

		self.paid_amount = total_paid
		self.unpaid_amount = total_unpaid

	def get_total_loan(self):
		total_loan = 0
		if self.loan_amount and self.payment_frequency:
			multiplier = 2 if self.payment_frequency == 'Both' else 1

			interest = self.loan_amount * (flt(self.interest,2) / 100)
			self.total_loan = flt(self.loan_amount + interest, 2)

		return total_loan

	def validate_user_sensitivity_level(self):
		cur_user = frappe.session.user
		if not "Administrator" in frappe.get_roles(cur_user):
			employeee_list = []

			employees = frappe.db.sql("""SELECT `parent` FROM `tabSensitivity Users` WHERE `allow_user` = %(user)s GROUP BY `parent`""",{ 
				"user": frappe.session.user,
			}, as_dict=True)
			for emp in employees:
				employeee_list.append(emp.parent)

			emp_sensitivity = frappe.db.get_value("Employee", self.employee, "sensitivity")
			if emp_sensitivity not in employeee_list:
				frappe.throw(_(" You dont have access to this employee "))
