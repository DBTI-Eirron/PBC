# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe 
from frappe.utils import flt, getdate, today
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

class Appraisal(Document):
	def validate(self):
		self.validate_fields()
		self.validate_rating()
		

	def on_submit(self):
		frappe.db.set(self, 'status', 'Submitted/Completed')
		frappe.db.set(self, 'date_completed', getdate(today()))

	def on_cancel(self):
		frappe.db.set(self, 'status', 'Cancelled')


	def get_employee_name(self):
		self.appraisee_name = frappe.db.get_value("Employee", self.appraisee, "full_name")
		return self.appraisee_name


	def get_performance_planning(self):
		kra = frappe.db.sql("""SELECT PP.type,PP.header,PP.department,PP.appraisee,PP.company,PP.appraisee_name,PP.from_date,PP.to_date,PP.date_joined,PP.job_title,KI.key_result_area,KI.key_indicator,KI.weight FROM `tabTarget Setting` PP INNER JOIN `tabPerformance Planning KI` KI ON KI.parent = PP.name WHERE PP.name = %s ORDER BY KI.`idx` ASC""",(self.target_setting),as_dict=True)
		entries = []
		for d in kra:
			self.appraisee = d.appraisee
			self.header = d.header
			self.target_setting_period = d.planning_period
			self.appraisee_name = d.appraisee_name
			self.department = d.department
			self.job_title = d.job_title
			self.date_joined = d.date_joined
			self.company = d.company
			self.type = d.type
			self.from_date = d.from_date
			self.to_date = d.to_date
			row = {
				"key_indicator":d.key_indicator,
				"weightage":d.weight
			}
			entries.append(row);
		for d in entries:
			row = self.append('appraisal_goal', {})
			row.update(d)
			
		return self.type

	def validate_fields(self):
		total_score = total_weight = 0 
		for indicator in self.appraisal_goal:
			total_score += indicator.score_earned
			total_weight += indicator.weightage
		self.total_score = total_score
		self.total_weight = total_weight

		if self.total_weight > 100:
			frappe.throw("Total Weight Must Be Less Than 100")

	def validate_rating(self):
		rating = frappe.db.sql("""SELECT rate_from, rate_to, name FROM `tabRating Classification`""",as_dict=True)
		for d in rating:
			if self.total_score <= float(d.rate_to) and self.total_score >= float(d.rate_from):
				self.equivalent_rating = d.name