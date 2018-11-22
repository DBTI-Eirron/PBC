# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate
from frappe import _
from frappe.model.document import Document

class LearningEvent(Document):
	def on_update_after_submit(self):
		if self.event_status == "Completed":
			self.create_evaluation_entries()

	def before_submit(self):
		if self.event_status == "Completed":
			self.create_evaluation_entries()

	def create_evaluation_entries(self):
		for d in self.participants:
			exist = frappe.db.sql("""SELECT `name` FROM `tabEvaluation for Learners` WHERE `event` = %s AND `session` = %s AND `employee` = %s """, (self.event_name, self.learning_program, d.employee), as_dict=True)
			if not exist:
				eval_entry = frappe.new_doc("Evaluation for Learners")
				eval_entry.update({
					"event": self.event_name,
					"program": self.learning_program,
					"employee": d.employee,
					"comment": "None",
				})

				eval_entry.insert()
				eval_entry.save()
			else:
				frappe.throw(_("Evaluation already exist"))

	def make_certificates(self):
		for d in self.participants:
			exist = frappe.db.sql("""SELECT `name` FROM `tabCertificate of Training` WHERE `training` = %s AND `date` = %s AND `employee` = %s """, (self.learning_program, nowdate(), d.employee), as_dict=True)
			if not exist:
				cert_entry = frappe.new_doc("Certificate of Training")
				cert_entry.update({
					"training": self.learning_program,
					"date": nowdate(),
					"employee": d.employee,
				})

				cert_entry.insert()
				cert_entry.save()
			else:
				frappe.throw(_("Certificate already exist"))