# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class TransactionType(Document):
	def validate(self):
		self.validate_birtype()

	def validate_birtype(self):
		tax_types = ["Representation", "Transportation", "COLA", "Housing Allowance","Fees","Commision","Profit Sharing", "Other Regular A", "Other Regular B", "Other Supplementary A", "Other Supplementary B"]
		non_tax_types = []

		if not self.is_taxable:
			if self.bir_type in tax_types:
				frappe.throw(_("BIR  Type <b>{0}</b> must be Taxable").format(self.bir_type))

	def on_trash(self):
		if self.is_standard == 1:
			frappe.throw(_("Cannot delete Standard Transaction Type"))