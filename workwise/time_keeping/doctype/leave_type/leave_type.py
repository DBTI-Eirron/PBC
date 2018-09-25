# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class LeaveType(Document):
	def validate(self):
		self.remove_duplicates()

	def remove_duplicates(self):
		unique_ent = []
		unique_entries = []
		for d in self.leave_type_table:
			if d.employment_status not in unique_ent:
				unique_ent.append(d.employment_status);

				i = {
					"employment_status": d.employment_status
				}	
				unique_entries.append(i);

		self.set('leave_type_table', [])
		for ue in unique_entries:
			row = self.append('leave_type_table', {})
			row.update(ue)