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
		existing_employees = []
		entry_employees = []
		for d in self.participants:
			if d.status == "Present":
				exist = frappe.db.sql("""SELECT `name` FROM `tabEvaluation for Learners` WHERE `event` = %s AND `program` = %s AND `employee` = %s """, (self.name, self.learning_program, d.employee), as_dict=True)
				if exist:
					existing_employees.append(d.employee)
				else:
					entry_employees.append(d.employee)

		for ent in entry_employees:
			parent = frappe.db.sql(""" SELECT `parent` FROM `tabLearning Evaluation Template Table Apply For` WHERE `apply_for` = %s """, (self.name), as_dict=True)
			if parent:
				for p in parent:
					if frappe.db.get_value("Learning Evaluation Template", p.parent, "type") == "Evaluation for Learners":
						items = frappe.db.sql(""" SELECT `items_for_evaluation` FROM `tabLearning Evaluation Template Table` WHERE `parent` = %s ORDER BY `idx` ASC """, (p.parent), as_dict=True)

						eval_entry = frappe.new_doc("Evaluation for Learners")
						eval_entry.update({
							"event": self.name,
							"program": self.learning_program,
							"employee": ent,
							"comment": "None",
							"company": frappe.get_value("Employee", ent, "company"),
							"department": frappe.get_value("Employee", ent, "department")
						})
						for i in items:
							eval_entry.append('evaluation_table',{
								"items": i.items_for_evaluation,
								"rating": 0.00,
							})
			
						eval_entry.insert()
						eval_entry.save()

		if existing_employees:
			existing_employees_list = ", ".join(str(x) for x in existing_employees)
			frappe.msgprint(_("Evaluation already exist for <br> {0} ").format(existing_employees_list))

	def create_session_evaluation_entries(self):
		session_list = []
		existing_employees = []
		entry_employees = []
		sessions = frappe.db.sql(""" SELECT `session` FROM `tabLearning Session Table` WHERE `parent` = %s ORDER BY `idx` ASC """, (self.name), as_dict=True)
		if sessions:
			session_list.append(self.name)
		else:
			session_list.append(self.learning_program)

		for d in self.participants:
			if d.status == "Present":
				for ses in session_list:
					exist = frappe.db.sql(""" SELECT `name` FROM `tabLearning Session Evaluation` WHERE `learning_event` = %s AND `learning_session` = %s AND `rated_by` = %s """, (self.name, ses, d.employee), as_dict=True)
					if exist:
						existing_employees.append(d.employee)
					else:
						entry_employees.append(d.employee)
						
		for ent in entry_employees:
			parent = frappe.db.sql(""" SELECT `parent` FROM `tabLearning Evaluation Template Table Apply For` WHERE `apply_for` = %s """, (self.name), as_dict=True)
			if parent:
				for p in parent:
					if frappe.db.get_value("Learning Evaluation Template", p.parent, "type") == "Session Evaluation":
						items = frappe.db.sql(""" SELECT `items_for_evaluation` FROM `tabLearning Evaluation Template Table` WHERE `parent` = %s ORDER BY `idx` ASC """, (p.parent), as_dict=True)
						eval_entry = frappe.new_doc("Learning Session Evaluation")
						eval_entry.update({
							"learning_session": ses,
							"learning_event": self.name,
							"rated_by": ent,
							"company": frappe.get_value("Employee", ent, "company")
						})

						for i in items:
							eval_entry.append('evaluation_table',{
								"items": i.items_for_evaluation,
								"rating": 0.00,
							})

						eval_entry.insert()
						eval_entry.save()

		if existing_employees:
			existing_employees_list = ", ".join(str(x) for x in existing_employees)
			frappe.msgprint(_("Session Evaluation already exist for <br> {0}").format(existing_employees_list))

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

	def get_learning_program(self):
		self.target_schedule = None
		self.venue = None
		self.session = None

		self.target_schedule = frappe.db.get_value("Learning Program", self.learning_program, "target_schedule")
		self.venue = frappe.db.get_value("Learning Program", self.learning_program, "venue")

		session_list = frappe.db.sql(""" SELECT `objective`, `methodology`, `session`, `target_schedule`, `venue` FROM `tabLearning Session Table` 
			WHERE `parent` = %s ORDER BY `idx` ASC """, (self.learning_program), as_dict=True)

		for s in session_list:
			ue = {
				"objective": s.objective,
				"methodology": s.methodology,
				"session": s.session,
				"target_schedule": s.target_schedule,
				"venue": s.venue,
			}

			row = self.append('session', {})
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
