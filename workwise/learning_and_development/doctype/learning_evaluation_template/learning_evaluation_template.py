# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class LearningEvaluationTemplate(Document):
	def validate(self):
		#self.validate_duplicate_template()
		self.remove_duplicate_entries()

	def remove_duplicate_entries(self):
		unique_ent = []
		unique_entries = []

		for d in self.apply_for:
			if str(d.apply_for) not in unique_ent:
				unique_ent.append(str(d.apply_for));

				i = {
					"apply_for": d.apply_for,
				}	
				unique_entries.append(i);

		self.set('apply_for', [])
		for ue in unique_entries:
			row = self.append('apply_for', {})
			row.update(ue)

	def validate_duplicate_template(self):
		exist = frappe.db.sql("""SELECT AF.`parent`, ET.`type` FROM `tabLearning Evaluation Template Table Apply For` AF 
			INNER JOIN `tabLearning Evaluation Template` ET ON AF.`parent`=ET.`name` WHERE AF.`apply_for` != %s LIMIT 1 """,(self.name), as_dict=True)

		if exist:
			if exist[0].type == self.type:
				frappe.throw(_("Evaluation {0} is already used in {1} ").format(self.name, exist[0].parent))
