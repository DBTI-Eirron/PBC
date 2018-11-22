# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class CoreValuesPractice(Document):
	def display_settings_value(self):
		entries = []
		description = frappe.db.get_single_value('Core Values Practice Settings', 'description')
		self.description = description
		indicators = frappe.db.sql("""SELECT values_indicator FROM `tabCore Values Practice Settings Table`""",as_dict=True)
		for d in indicators:
			row = {
				"values_indicator": d.values_indicator,
			}
			entries.append(row);

		for d in entries:
			row = self.append('values_indicator', {})
			row.update(d)
