# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate
from frappe import _
from frappe.model.document import Document

class LearningProgram(Document):
	def validate(self):
		self.validate_duplicate_entry_in_tables()
		self.compute_participants_total_cost()
		self.compute_total_needs_cost()

	def on_submit(self):
		pass

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

	def compute_participants_total_cost(self):
		i = 0
		for d in self.participants:
			i += 1

		self.total_cost_participant = flt(self.cost_per_participant, 2) * i

	def compute_total_needs_cost(self):
		for d in self.needs:
			self.total_cost_materials = flt(self.total_cost_materials, 2) + (flt(d.cost, 2) * flt(d.quantity, 2))