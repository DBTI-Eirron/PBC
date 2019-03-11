# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.model.document import Document

class LearningParticipantsStatus(Document):
	def validate(self):
		for d in self.get('participants'):
			if d.new_status:
				frappe.db.sql("""UPDATE `tabLearning Participants` SET `status` = %s WHERE `parent` = %s AND `employee` = %s """,( d.new_status, self.learning_event, d.employee ), as_dict=True )
				frappe.db.commit()
		self.create_evaluation_entries()

	def create_evaluation_entries(self):
		for d in self.participants:
			if d.new_status == "Present":
				exist = frappe.db.sql("""SELECT `name` FROM `tabEvaluation for Learners` WHERE `event` = %s AND `program` = %s AND `employee` = %s """, (self.learning_event, self.learning_program, d.employee), as_dict=True)
				if not exist:
					eval_entry = frappe.new_doc("Evaluation for Learners")
					eval_entry.update({
						"event": self.learning_event,
						"program": self.learning_program,
						"employee": d.employee,
						"comment": "None",
					})

					eval_entry.insert()
					eval_entry.save()
				else:
					frappe.msgprint(_("Evaluation for {0} already exist").format(d.employee_name))