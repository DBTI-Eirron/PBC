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
		for d in self.get('payments'):
			if self.freq_method == "Automatic":
				frappe.db.sql("""UPDATE `tabLoan Application Payments` SET payment_amount = %s WHERE parent = %s AND idx = %s  """,( flt(d.new_amount, 8), self.loan_id, d.target_idx ), as_dict=True )
			else:
				frappe.db.sql("""UPDATE `tabLoan Application Payments` SET payment_amount = %s, due_date = %s WHERE parent = %s AND idx = %s  """,( flt(d.new_amount, 8), d.new_due_date, self.loan_id, d.target_idx ), as_dict=True )

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
