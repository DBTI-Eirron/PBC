# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class LearningEvent(Document):
	def validate(self):
		pass

	def on_submit(self):
		self.create_evaluation_entries()

	def create_evaluation_entries(self):
		participants = frappe.db.sql("""SELECT * FROM `tabLearning Participants` WHERE `parenttype` = "Learning Program" and `parent` = %s """, (self.learning_program), as_dict=True)
		objectives = frappe.db.sql("""SELECT * FROM `tabLearning Objective Table` WHERE `parenttype` = "Learning Program" and `parent` = %s """, (self.learning_program), as_dict=True)
		for d in participants:
			eval_entry = frappe.new_doc("Learning Evaluation")
			eval_entry.update({
				"event_type": "Learning Event",
				"event": self.name,
				"employee": d.employee
			})

			for a in objectives:
				eval_entry.append('evaluation_table',{
					"objective": a.objective,
					"grade": 0
				})

			eval_entry.insert()
			eval_entry.save()