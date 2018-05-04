# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import get_datetime, today, cstr
from frappe import throw, _, scrub
from frappe.model.document import Document

class IncidentReport(Document):
	
	def validate(self):
		self.validate_datetime()
		self.validate_memo()

	def on_submit(self):
		self.make_memo()

	def validate_datetime(self):
		if self.date_time_offense and get_datetime(self.date_time_offense) > get_datetime(today()):
			throw(_("Date and Time of Incident cannot be greater than today."))

	def make_memo(self):
		for d in self.involved_employees:
			new_memo = frappe.new_doc("Memo")
			new_memo.update({
				"employee": d.employee,
				"involvement": d.involvement,
				"department": d.department,
				"offense": self.offense,
			})

			new_memo.insert()

	def validate_memo(self):
		check_list = []
		for d in self.involved_employees:
			check_list.append(cstr(d.employee))

		unique_chk_list = set(check_list)
		if len(unique_chk_list) != len(check_list):
			throw(_("Same Employee has been entered multiple times"))