# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe 
from frappe.utils import flt, getdate, today
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document


class Evaluation(Document):
	def validate(self):
		self.validate_fields()
		self.validate_rating()

	def on_submit(self):
		frappe.db.set(self, 'date_completed', getdate(today()))
		self.validate_score()

	def get_employee_name(self):
		self.appraisee_name = frappe.db.get_value("Employee", self.appraisee, "full_name")
		return self.appraisee_name


	def get_performance_planning(self):
		kra = frappe.db.sql("""SELECT PP.from_date,PP.to_date,KI.key_result_area,KI.key_indicator,KI.weight FROM `tabTarget Settings` PP INNER JOIN `tabPerformance Planning KI` KI ON KI.parent = PP.name WHERE PP.name = %s ORDER BY KI.`idx` ASC""",(self.target_setting),as_dict=True)
		entries = []
		for d in kra:
			self.target_setting_period = d.planning_period
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

	def validate_fields(self):
		total_score = total_weight = 0 
		for indicator in self.appraisal_goal:
			total_score += flt(indicator.score_earned)
			total_weight += flt(indicator.weightage)
		self.total_score = total_score
		self.total_weight = total_weight

		if self.total_weight > 100:
			frappe.throw("Total Weight Must Be Less Than 100")

	def validate_rating(self):
		rating = frappe.db.sql("""SELECT rate_from, rate_to, name FROM `tabRating Classification`""",as_dict=True)
		for d in rating:
			if self.total_score <= float(d.rate_to) and self.total_score >= float(d.rate_from):
				self.equivalent_rating = d.name

	def validate_score(self):
		if self.equivalent_rating == "Did Not Meed Expectations (DME)" or self.equivalent_rating == "Barely Meets Expections(BME)":
			pip = frappe.db.sql_list("""SELECT COUNT(`name`) FROM `tabPerformance Improvement Plan` WHERE evaluation = '%s' AND employee = %s""",(self.name,self.appraisee))
			frappe.throw(_(pip))
			if pip <= 0:
				frappe.throw(_("Create Performance Improvement Plan"))