# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class InterviewandBackground(Document):
	def on_submit(self):
		self.update_applicant_status()

	def update_applicant_status(self):
		frappe.db.sql(""" Update `tabSchedules and Assessment` SET apply_type='Job Offer', interview_date= %s where name=%s""", (self.interview_date, self.schedule))
		self.db_set("apply_type", "Job Offer")