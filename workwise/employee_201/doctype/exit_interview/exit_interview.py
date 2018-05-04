# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

class ExitInterview(Document):
	pass

@frappe.whitelist()
def make_movement(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.movement_type = frappe.db.get_value("Exit Interview", source.employee, "exit_type")

	doc = get_mapped_doc("Exit Interview", source_name, {
			"Exit Interview": {
				"doctype": "Employee Movement",
				"field_map": {
					"exit_type": "movement_type"
				}}
		}, target_doc, set_missing_values)
	return doc
