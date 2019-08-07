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

	def get_evaluation_items(self):
		self.evaluation_table = None

		parent = frappe.db.sql(""" SELECT `parent` FROM `tabLearning Evaluation Template Table Apply For` WHERE `apply_for` = %s """, (self.event), as_dict=True)
		if parent:
			for p in parent:
				if frappe.db.get_value("Learning Evaluation Template", p.parent, "type") == "Evaluation for Learners":
					items = frappe.db.sql(""" SELECT `items_for_evaluation` FROM `tabLearning Evaluation Template Table` WHERE `parent` = %s ORDER BY `idx` ASC """, (p.parent), as_dict=True)

					for i in items:
						ue = {
							"items": i.items_for_evaluation,
							"rating": 0.00,
						}

						row = self.append('evaluation_table', {})
						row.update(ue)
