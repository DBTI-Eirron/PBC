# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.utils import cint, flt, getdate, cstr, nowdate
from frappe.model.document import Document

class LoanRestructure(Document):
	def validate(self):
		self.validate_payment_amount()
		self.validate_loan_amount()

	def on_submit(self):
		target_idx = 0
		total_paid, total_unpaid = 0, 0

		for d in self.get('payments'):
			if self.freq_method == "Automatic":
				frappe.db.sql("""UPDATE `tabLoan Application Payments` SET payment_amount = %s WHERE parent = %s AND idx = %s  """,( flt(d.new_amount, 8), self.loan_id, d.target_idx ), as_dict=True )
				target_idx = d.target_idx
			else:
				frappe.db.sql("""UPDATE `tabLoan Application Payments` SET payment_amount = %s, due_date = %s WHERE parent = %s AND idx = %s  """,( flt(d.new_amount, 8), d.new_due_date, self.loan_id, d.target_idx ), as_dict=True )
				target_idx = d.target_idx
		
		if target_idx:
			frappe.db.sql("""DELETE FROM `tabLoan Application Payments` WHERE `idx` > %s  AND parent = %s""",(target_idx, self.loan_id), as_dict=1)
		
		payments = frappe.db.sql("""SELECT payment_status, payment_amount FROM `tabLoan Application Payments` 
			WHERE parent = %s""",(self.loan_id), as_dict=True )
		
		for p in payments:
			if p.payment_status == 'Paid':
				total_paid += p.payment_amount
			else:
				total_unpaid += p.payment_amount

		frappe.db.sql("""UPDATE `tabLoan Application` SET unpaid_amount = %s, paid_amount = %s
			WHERE name = %s LIMIT 1 """,(total_unpaid, total_paid, self.loan_id), as_dict=True )

		doc = frappe.get_doc("Loan Application", self.loan_id)
		doc.run_method("update_loan_status")
		doc.save()
		
	def validate_payment_amount(self):
		amount = 0.0
		for d in self.get('payments'):
			amount += d.new_amount

		self.restructured_amount = amount

	def validate_loan_amount(self):
		amount = 0.0
		for d in self.get('payments'):
			amount += d.new_amount

		if flt(amount, 2) != flt(self.unpaid_amount, 2):
			frappe.throw(_(" Amount in Payments is not equal to Unpaid Amount"))
