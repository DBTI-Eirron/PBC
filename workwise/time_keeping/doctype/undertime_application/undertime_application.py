# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import datetime
from frappe import _
from frappe.utils import nowdate, get_time, flt
from frappe.model.document import Document

class UndertimeApplication(Document):
	def validate(self):
		total_hrs = datetime.strptime(self.to_time, '%H:%M:%S') - datetime.strptime(self.from_time, '%H:%M:%S')
		self.total_hrs = flt((total_hrs.total_seconds() / 60.0 / 60.0),2)

	def on_submit(self):
		self.get_approver_and_date()

	def on_cancel(self):
		pass

	def get_approver_and_date(self):
		self.approved_by = frappe.session.user
		self.approved_on = nowdate()