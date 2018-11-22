# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate
from frappe import _
from frappe.model.document import Document

class EvaluationforLearners(Document):
	def validate(self):
		self.calculate_final_grade()

	def on_submit(self):
		self.calculate_final_grade()

	def before_submit(self):
		self.evaluation_date = nowdate()
		self.evaluated_by = frappe.session.user

	def calculate_final_grade(self):
		i = 1
		final_g = 0
		for d in self.evaluation_table:
			i += 1
			final_g	+= flt(d.rating, 2)
		final_grade = flt(final_g, 2) / i - 1
		if final_grade < 0:
			final_grade = 0
		self.average_rating = flt(final_grade, 2)