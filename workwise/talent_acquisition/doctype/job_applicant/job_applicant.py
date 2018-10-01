# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, validate_email_add, today, add_years
from frappe import throw, _, scrub

class JobApplicant(Document):

	def validate(self):
		self.update_applicant_name()
		self.validate_date()
		self.validate_company()
		if not self.apply_type:
			self.apply_type = "Candidate"

	def on_submit(self):
		self.update_applicant_status()

	def update_applicant_name(self):
		if self.middle_name:
			self.applicant_name = str(self.last_name) + ', ' + str(self.first_name) + ' ' + str(self.middle_name)
		else:
			self.applicant_name = str(self.last_name) + ', ' + str(self.first_name)

	def validate_date(self):
		if self.application_date and getdate(self.application_date) > getdate(today()):
			throw(_("Date of Application cannot be greater than today."))

	def validate_company(self):
		if self.currently_employed == "No":
			self.company = ""

		if self.currently_employed == "Yes": 
			if not self.company:
				throw(_("Company is required"))

	def update_applicant_status(self):
		self.db_set("apply_type", "For Assessment")