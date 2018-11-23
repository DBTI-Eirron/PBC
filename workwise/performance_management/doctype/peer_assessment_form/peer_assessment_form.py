# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PeerAssessmentForm(Document):
	def validate(self):
		self.check_table()

	def check_table(self):
		temp = 0 
		for values in self.values_indicator:
			if values.rating is None or values.evidence is None:
				temp += 1
		if temp > 0:
			frappe.throw("Rating and Evidence is Mandatory")