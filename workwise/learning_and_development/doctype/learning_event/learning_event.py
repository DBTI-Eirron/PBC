# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class LearningEvent(Document):
	def validate(self):
		self.validate_duplicate_entry()

	def before_submit(self):
		self.create_evaluation_entries()
		self.create_session_evaluation_entries()

	def create_evaluation_entries(self):
		for d in self.participants:
			if d.status == "Present":
				exist = frappe.db.sql("""SELECT `name` FROM `tabEvaluation for Learners` WHERE `event` = %s AND `program` = %s AND `employee` = %s """, (self.event_name, self.learning_program, d.employee), as_dict=True)
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
					frappe.msgprint(_("Evaluation for {0} already exist").format(d.employee_name))

	def create_session_evaluation_entries(self):
		for d in self.participants:
			if d.status == "Present":
				session_list = frappe.db.sql("""SELECT DISTINCT `session` FROM `tabLearning Session Table` WHERE `parent`=%s """, (self.learning_program), as_dict=True)
				for ses in session_list:
					exist = frappe.db.sql("""SELECT DISTINCT `name` FROM `tabLearning Session Evaluation` WHERE `learning_event`=%s AND `learning_session`=%s AND `employee`=%s """, (self.name, ses.session, d.employee), as_dict=True)
					if not exist:
						eval_entry = frappe.new_doc("Learning Session Evaluation")
						eval_entry.update({
							"learning_event": self.name,
							"learning_session": ses.session,
							"employee": d.employee,
						})

						eval_entry.insert()
						eval_entry.save()
					else:
						frappe.msgprint(_("Session {1} Evaluation for {0} already exist").format(d.employee_name, ses.session))

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

	def validate_duplicate_entry(self):
		unique_ent = []
		unique_entries = []

		for d in self.get("participants"):
			if str(d.employee+d.employee_name) not in unique_ent:
				unique_ent.append(str(d.employee+d.employee_name));
				ent = { 
					"employee": d.employee,
					"employee_name": d.employee_name,
					"company": d.company,
					"department": d.department,
					"status": d.status,
				}
				unique_entries.append(ent);

			self.set('participants', [])
			for ue in unique_entries:
				row = self.append('participants', {})
				row.update(ue)

@frappe.whitelist()
def update_status(source_name, target_doc=None):
	def add_entries(source, target):
		entries = []
		for d in source.participants:
			ent = { 
				"employee": d.employee,
				"employee_name": d.employee_name,
				"company": d.company,
				"old_status": d.status,
			}
			entries.append(ent)

		for d in entries:
			row = target.append('participants', {})
			row.update(d)

	def update_target(source_doc, target_doc, source_parent):
		target_doc.learning_event = source_doc.name
		target_doc.learning_program = source_doc.learning_program

	doclist = get_mapped_doc("Learning Event", source_name, {
		"Learning Event": {
			"doctype": "Learning Participants Status",
			"validation": {
				"docstatus": ["=", 1]
			},
			"postprocess": update_target
		}
	}, target_doc, add_entries)

	return doclist