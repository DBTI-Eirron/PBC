# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document

class ServiceAgreementContract(Document):
	def validate(self):
		self.total_training_cost = flt(self.training_cost, 2) + flt(self.previous_training_cost, 2)
