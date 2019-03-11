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
		i = 0
		a = 0
		final_g = 0
		for d in self.session_table:
			i += 1
			final_g	+= flt(d.rating, 2)

		for f in self.facilitator_table:
			a += 1
			final_g	+= flt(f.rating, 2)

		divisor = i + a
		if divisor > 0:
			final_grade = flt(final_g, 2) / flt(divisor, 2)
		else:
			final_grade = flt(final_g, 2) / 1

		self.average_rating = flt(final_grade, 2)