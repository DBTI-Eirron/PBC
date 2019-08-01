# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class WLDNeeds(Document):
	def validate(self):
		self.validate_duplicate_entry()
		self.prompt_message()

	def prompt_message(self):
		frappe.msgprint('If you are done with this please submit.')

	def validate_duplicate_entry(self):
		unique_ent = []
		unique_entries = []

		for d in self.get("wld_needs"):
			if str(d.employee+d.employee_name+d.training) not in unique_ent:
				unique_ent.append(str(d.employee+d.employee_name+d.training));
				ent = { 
					"employee": d.employee,
					"employee_name": d.employee_name,
					"training": d.training,
					"provider": d.provider,
					"purpose": d.purpose,
					"budget": d.budget,
					"status": d.status,
					"target_date": d.target_date,
				}
				unique_entries.append(ent);

			self.set('wld_needs', [])
			for ue in unique_entries:
				row = self.append('wld_needs', {})
				row.update(ue)

@frappe.whitelist()
def update_status(source_name, target_doc=None):
	def add_entries(source, target):
		entries = []
		for d in source.wld_needs:
			ent = { 
				"employee": d.employee,
				"employee_name": d.employee_name,
				"old_status": d.status,
				"new_status": d.status,
				"training": d.training,
			}
			entries.append(ent)

		for d in entries:
			row = target.append('status_table', {})
			row.update(d)

	def update_target(source_doc, target_doc, source_parent):
		target_doc.wld_needs_id = source_doc.name

	doclist = get_mapped_doc("WLD Needs", source_name, {
		"WLD Needs": {
			"doctype": "WLD Needs Status",
			"validation": {
				"docstatus": ["=", 1]
			},
			"postprocess": update_target
		}
	}, target_doc, add_entries)

	return doclist