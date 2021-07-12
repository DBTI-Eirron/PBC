# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from dateutil import relativedelta
from dateutil.rrule import *
from frappe import _
from frappe.utils import cint, flt, getdate, cstr, nowdate
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from workwise.time_keeping.application_utils import validate_inactive_employee

class LoanApplication(Document):
	def validate(self):
		self.validate_loan()
		validate_inactive_employee(self)
		self.get_sensitivity_level()
		self.update_missing_names()
		self.update_paid_unpaid()
		self.validate_date()
		self.validate_user_sensitivity_level()
		self.update_amounts()
		self.update_loan_status()

	def on_change(self):
		self.update_loan_status()

	def validate_loan(self):
		loan_type = frappe.db.sql("""SELECT `name` FROM `tabTransaction Type` WHERE `code` = %s and `entry_type` = 'Loan'""", self.loan_type, as_dict=True)
		if not loan_type:
			frappe.throw(_("Incorrect Loan Type"))

	def update_missing_names(self):
		self.employee_name = frappe.db.get_value("Employee", self.employee, "full_name")
		self.loan_name = frappe.db.get_value("Transaction Type", self.loan_type, "title")

	def validate_date(self):
		if self.release_date > self.payment_start:
			frappe.throw(("Release Date should not be greater than Payment Start")) 

	def update_amounts(self):
		entries = []
		if self.docstatus == 0 and self.loan_amount and self.amortization:
			self.set('payments', [])
			if self.freq_method == "Automatic":
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
						"payment_date": self.release_date,
					});

				while total_payables > 0:
					pay_amount = flt(self.amortization) / multiplier
					if not total_payables >= pay_amount:
						pay_amount = total_payables

					info = {"payment_amount": pay_amount, "payment_status": "Unpaid", "payment_date": None}

					total_payables -= pay_amount
					entries.append(info);

			elif self.freq_method == "Relative Month" or self.freq_method == "Relative Days":
				multiplier = 1

				total_loan =  self.loan_amount + (self.loan_amount * (flt(self.interest,2) / 100)) if self.interest > 0 else self.loan_amount
				self.total_loan = total_loan

				unpaid_amount = total_loan - self.beginning_balance if self.beginning_balance > 0 else total_loan

				if self.beginning_balance >= total_loan:
					frappe.throw(("Beginning Balance should not be greater than Total Loan")) 
					
				total_payables = unpaid_amount 
				actual_beginning_balance = self.beginning_balance
				start = datetime.datetime.strptime(self.payment_start, '%Y-%m-%d')
				
				if self.freq_method == "Relative Month":
					relative = cint(self.relative_month) or 1 
					step = relativedelta.relativedelta(months=relative)
				elif self.freq_method == "Relative Days":
					relative = cint(self.relative_days) or 1 
					step = relativedelta.relativedelta(days=relative)


				if self.beginning_balance:
					entries.append({
						"payment_amount": self.beginning_balance,
						"payment_status": "Paid",
						"payment_date": self.release_date,
					});

				while total_payables > 0:
					pay_amount = flt(self.amortization) / multiplier
					if not total_payables >= pay_amount:
						pay_amount = total_payables
						
					info = {"due_date": getdate(start), "payment_amount": pay_amount, "payment_status": "Unpaid", "payment_date": None}
					total_payables -= pay_amount

					start += step
					
					entries.append(info);

			elif self.freq_method == "Date":
				multiplier = 1

				total_loan =  self.loan_amount + (self.loan_amount * (flt(self.interest, 2) / 100)) if self.interest > 0 else self.loan_amount
				self.total_loan = total_loan

				unpaid_amount = total_loan - self.beginning_balance if self.beginning_balance > 0 else total_loan

				if self.beginning_balance >= total_loan:
					frappe.throw(("Beginning Balance should not be greater than Total Loan")) 
					
				total_payables = unpaid_amount
				actual_beginning_balance = self.beginning_balance
				start = datetime.datetime.strptime(self.payment_start, '%Y-%m-%d')
				bymonthday = self.first_date

				if self.second_date in [29, 30, 31]:
					second_date = -1
				else:
					second_date = self.second_date

				days = rrule(MONTHLY, dtstart=start, bymonthday=(self.first_date, second_date))				
				count = 0

				if self.beginning_balance:
					entries.append({
						"payment_amount": self.beginning_balance,
						"payment_status": "Paid",
						"payment_date": self.release_date,
					});

				while total_payables > 0:
					pay_amount = flt(self.amortization) / multiplier
					if not total_payables >= pay_amount:
						pay_amount = total_payables
						
					info = {"due_date": getdate(days[count]), "payment_amount": pay_amount, "payment_status": "Unpaid", "payment_date": None}
					total_payables -= pay_amount

					entries.append(info)
					count += 1

		for d in entries:
			row = self.append('payments', {})
			row.update(d)

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

	def get_sensitivity_level(self):
		self.sensitivity_level = frappe.db.get_value("Employee", self.employee, 'sensitivity')

	def update_loan_status(self):
		if self.docstatus != 0:
			status = "Entered"
			if self.on_hold:
				status = "On Hold"
			elif not self.on_hold and flt(self.unpaid_amount) == 0:
				status = "Fully Paid"
			elif not self.on_hold and flt(self.paid_amount) < 1 and flt(self.unpaid_amount) > 0:
				status = "Entered"
			elif not self.on_hold and flt(self.paid_amount) > 0 and flt(self.unpaid_amount) > 0:
				status = "Active"
			self.status = status

@frappe.whitelist()
def make_restructure(source_name, target_doc=None):
	def add_entries(source, target):
		entries = []
		target.set("accounts", [])
		for d in source.payments:
			if d.payment_status == "Unpaid":
				pay = { 
					"target_idx": d.idx,
					"old_due_date": d.due_date,
					"new_due_date": d.due_date,
					"old_amount": d.payment_amount,
					"new_amount": d.payment_amount,
				}
				entries.append(pay)

		for d in entries:
			row = target.append('payments', {})
			row.update(d)

	def update_target(source_doc, target_doc, source_parent):
		target_doc.loan_id = source_doc.name
		target_doc.total_loan_amount = source_doc.total_loan
		target_doc.employee = source_doc.employee
		target_doc.employee_name = source_doc.employee_name
		target_doc.freq_method = source_doc.freq_method
		target_doc.sensitivity_level = source_doc.sensitivity_level

	doclist = get_mapped_doc("Loan Application", source_name, {
		"Loan Application": {
			"doctype": "Loan Restructure",
			"validation": {
				"docstatus": ["=", 1]
			},
			"postprocess": update_target
		}
	}, target_doc, add_entries)

	return doclist