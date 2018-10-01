# -*- coding: utf-8 -*-	
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class SchedulesandAssessment(Document):
	def on_submit(self):
		self.update_applicant_status()

	def update_applicant_status(self):
		frappe.db.sql(""" Update `tabJob Applicant` SET apply_type='For Interview', interview_date= %s where name=%s""", (self.scheduled_date, self.applicant))
		self.db_set("apply_type", "For Interview")
		
