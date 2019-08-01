# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.model.document import Document

class LearningParticipantsStatus(Document):
	def validate(self):
		self.create_evaluation_entries()
		self.create_session_evaluation_entries()
		for d in self.get('participants'):
			if d.new_status:
				frappe.db.sql("""UPDATE `tabLearning Participants` SET `status` = %s WHERE `parent` = %s AND `employee` = %s """,( d.new_status, self.learning_event, d.employee ), as_dict=True )
				frappe.db.commit()

	def create_evaluation_entries(self):
		existing_employees = []
		entry_employees = []
		for d in self.participants:
			if d.new_status == "Present":
				exist = frappe.db.sql("""SELECT `name` FROM `tabEvaluation for Learners` WHERE `event` = %s AND `program` = %s AND `employee` = %s """, (self.learning_event, self.learning_program, d.employee), as_dict=True)
				if exist:
					existing_employees.append(d.employee)
				else:
					entry_employees.append(d.employee)

		for ent in entry_employees:
			parent = frappe.db.sql(""" SELECT `parent` FROM `tabLearning Evaluation Template Table Apply For` WHERE `apply_for` = %s """, (self.learning_event), as_dict=True)
			if parent:
				for p in parent:
					if frappe.db.get_value("Learning Evaluation Template", p.parent, "type") == "Evaluation for Learners":
						items = frappe.db.sql(""" SELECT `items_for_evaluation` FROM `tabLearning Evaluation Template Table` WHERE `parent` = %s ORDER BY `idx` ASC """, (p.parent), as_dict=True)

						eval_entry = frappe.new_doc("Evaluation for Learners")
						eval_entry.update({
							"event": self.learning_event,
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
		sessions = frappe.db.sql(""" SELECT `session` FROM `tabLearning Session Table` WHERE `parent` = %s ORDER BY `idx` ASC """, (self.learning_event), as_dict=True)
		if sessions:
			session_list.append(self.learning_event)
		else:
			session_list.append(self.learning_program)

		for d in self.participants:
			if d.new_status == "Present":
				for ses in session_list:
					exist = frappe.db.sql(""" SELECT `name` FROM `tabLearning Session Evaluation` WHERE `learning_event` = %s AND `learning_session` = %s AND `rated_by` = %s """, (self.learning_event, ses, d.employee), as_dict=True)
					if exist:
						existing_employees.append(d.employee)
					else:
						entry_employees.append(d.employee)
						
		for ent in entry_employees:
			parent = frappe.db.sql(""" SELECT `parent` FROM `tabLearning Evaluation Template Table Apply For` WHERE `apply_for` = %s """, (self.learning_event), as_dict=True)
			if parent:
				for p in parent:
					if frappe.db.get_value("Learning Evaluation Template", p.parent, "type") == "Session Evaluation":
						items = frappe.db.sql(""" SELECT `items_for_evaluation` FROM `tabLearning Evaluation Template Table` WHERE `parent` = %s ORDER BY `idx` ASC """, (p.parent), as_dict=True)
						eval_entry = frappe.new_doc("Learning Session Evaluation")
						eval_entry.update({
							"learning_session": ses,
							"learning_event": self.learning_event,
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