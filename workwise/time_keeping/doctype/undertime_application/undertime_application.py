# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate, get_time
from frappe.model.document import Document

class UndertimeApplication(Document):
	def validate(self):
		pass

	def on_submit(self):
		self.get_approver_and_date()

	def on_cancel(self):
		pass

	def get_approver_and_date(self):
		self.approved_by = frappe.session.user
		self.approved_on = nowdate()