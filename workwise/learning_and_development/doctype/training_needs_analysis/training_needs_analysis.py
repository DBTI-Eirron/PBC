# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class TrainingNeedsAnalysis(Document):
	def validate(self):
		self.validate_duplicate_entry_in_tables()

	def on_submit(self):
		self.create_evaluation_entries()

	def validate_duplicate_entry_in_tables(self):
		unique_obj = []
		unique_entries_obj = []
		for d in self.objectives:
			if d.objective not in unique_obj:
				unique_obj.append(d.objective);
				
				i = {
					"objective": d.objective,
					"description": d.description
				}	
				unique_entries_obj.append(i);

		self.set('objectives', [])
		for uo in unique_entries_obj:
			row = self.append('objectives', {})
			row.update(uo)

		unique_emp = []
		unique_entries_emp = []
		for d in self.participants:
			if d.employee not in unique_emp:
				unique_emp.append(d.employee);
				
				i = {
					"employee": d.employee,
					"employee_name": d.employee_name,
					"company": d.company,
					"department": d.department
				}	
				unique_entries_emp.append(i);

		self.set('participants', [])
		for ue in unique_entries_emp:
			row = self.append('participants', {})
			row.update(ue)

	def create_evaluation_entries(self):
		for d in self.get("participants"):
			eval_entry = frappe.new_doc("Learning Evaluation")
			eval_entry.update({
				"event_type": "Training Needs Analysis",
				"event": self.name,
				"employee": d.employee
			})

			for a in self.get("objectives"):
				eval_entry.append('evaluation_table',{
					"objective": a.objective,
					"grade": 0
				})

			eval_entry.insert()
			eval_entry.save()