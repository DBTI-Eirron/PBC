# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint, throw
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class Interview(Document):
	def validate(self):
		self.validate_interview()
		self.calculate_score()

	def validate_interview(self):
		first = frappe.db.sql(""" SELECT *  FROM `tabInterview` WHERE `schedule` = %s AND interview_status = %s AND name != %s """, (self.schedule, "First", self.name), as_dict=1)
		second = frappe.db.sql(""" SELECT *  FROM `tabInterview` WHERE `schedule` = %s AND interview_status = %s AND name != %s """, (self.schedule, "Second", self.name), as_dict=1)
		third = frappe.db.sql(""" SELECT *  FROM `tabInterview` WHERE `schedule` = %s AND interview_status = %s AND name != %s """, (self.schedule, "Third", self.name), as_dict=1)
		
		interview_status = frappe.db.get_value("Schedules and Assessment", self.schedule, "interview_status")
		if interview_status == "Completed":
			frappe.throw(_("Cannot Create Completed Schedule for {0}").format(self.schedule))

		if interview_status =="First" and first:
			frappe.throw(_("First Interview for this Schedule Already exist "))
	
		elif interview_status == "Second" and second:
			frappe.throw(_("Second Interview for this Schedule Already exist"))

		elif interview_status == "Third" and third:
			frappe.throw(_("Third Interview for this Schedule Already exist "))

		if interview_status =="First":
			self.status_type = "Behavioral Interview"

		if interview_status =="Second":
			self.status_type = "Technical Interview"

		if interview_status =="Third":
			self.status_type = "Final Interview"

	def calculate_score(self):
		overall_score=0
		total_percentage=0
		for d in self.interview_result:
			if flt(d.score, 2) > 4 or flt(d.score, 2) < 1:
				frappe.throw(_(" Invalid Score for {0}").format(d.title))

			total_percentage += flt(d.percentage, 2)
			overall_score += (flt(d.score, 2) * (flt(d.percentage, 2) / 100) )

		self.total_percentage = total_percentage
		self.overall_score = (overall_score / 4) * 100

	def on_submit(self):
		self.update_applicant_status()

	def update_applicant_status(self):
		if self.interview_status == "First":
			frappe.db.sql(""" Update `tabSchedules and Assessment` SET interview_status='Second', status_type='Technical Interview' where name=%s""", (self.schedule))

		if self.interview_status == "Second":
			frappe.db.sql(""" Update `tabSchedules and Assessment` SET interview_status='Third', status_type='Final Interview' where name=%s""", (self.schedule))

		if self.interview_status == "Third":
			frappe.db.sql(""" Update `tabSchedules and Assessment` SET apply_type='Background Investigation', interview_status='Completed' where name=%s""", (self.schedule))
			self.db_set("apply_type", "Background Investigation")