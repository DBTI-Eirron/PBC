# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate
from frappe import _
from frappe.model.document import Document

class LearningSessionEvaluation(Document):
	def validate(self):
		self.calculate_final_grade()

	def get_items(self):
		table_list = ['session_table', 'facilitator_table']
		for t in table_list:
			self.set(t, [])
			slist = [
				{"item": "Achievement of the session’s Objectives"},
				{"item": "Content of the Learning Session"},
				{"item": "Presentation and workshop materials"},
				{"item": "Opportunities to ask questions and clarify issues"},
			]

			flist = [
				{"item": "Mastery of the subject matter"},
				{"item": "Ability to impart knowledge"},
				{"item": "Ability to answer questions/clarify issues"},
				{"item": "Manner of delivering the session"},
			]

			if t == "session_table":
				for s in slist:
					self.append(t, s)
			else:
				for f in flist:
					self.append(t, f)

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

		parent = frappe.db.sql(""" SELECT `parent` FROM `tabLearning Evaluation Template Table Apply For` WHERE `apply_for` = %s """, (self.learning_event), as_dict=True)
		if parent:
			for p in parent:
				if frappe.db.get_value("Learning Evaluation Template", p.parent, "type") == "Session Evaluation":
					items = frappe.db.sql(""" SELECT `items_for_evaluation` FROM `tabLearning Evaluation Template Table` WHERE `parent` = %s ORDER BY `idx` ASC """, (p.parent), as_dict=True)

					for i in items:
						ue = {
							"items": i.items_for_evaluation,
							"rating": 0.00,
						}

						row = self.append('evaluation_table', {})
						row.update(ue)