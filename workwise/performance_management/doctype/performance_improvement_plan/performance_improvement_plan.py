# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PerformanceImprovementPlan(Document):
	def get_appraisal(self):
		entries = []
		settings = frappe.db.sql("""SELECT key_indicator FROM `tabAppraisal Goal` WHERE score <= 2 AND parent = %s""",(self.appraisal),as_dict=True)
		for d in settings:
			row = {
				"performance_gaps":d.key_indicator,
			}
			entries.append(row);
		for d in entries:
			row = self.append('items', {})
			row.update(d)
			