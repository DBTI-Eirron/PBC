# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, ast
from frappe.utils import cint, flt, nowdate, cstr
from frappe import _, msgprint
from frappe.model.document import Document


class LearningParticipantsStatus(Document):
	def get_program_session(self):  
		option_list = ["All"]
		sessions = frappe.db.sql("""SELECT * FROM `tabLearning Session Table` WHERE `parent` = %s """, (self.learning_event), as_dict=True)
		
		option_list.append(self.learning_program)
		for s in sessions:
			option_list.append(s.session)

		return option_list

	def before_submit(self):
		self.save_attendance_changes()
		self.create_evaluation_entries()
		self.create_session_evaluation_entries()

	def get_attendance_data(self):
		participant_data = frappe.db.sql("""SELECT * FROM `tabLearning Participants` WHERE `parent` = %s """, (self.learning_event), as_dict=True)
		self.set('participants', [])
		for ue in participant_data:
			row = self.append('participants', {})
			ins = {
				"employee":  ue.employee,
				"employee_name": ue.employee_name,
				"company": ue.company,				
				"row_name": ue.name,
				"attendance_data": ue.attendance_data,
			}
			row.update(ins)

		if self.program_session != "All":
			for d in self.participants:
				d.old_status = None
				d.program_session = self.program_session
				if d.attendance_data:
					att_data_list = ast.literal_eval(d.attendance_data)
					if self.program_session in att_data_list:
						d.old_status = att_data_list[self.program_session]
		else:
			row_list = []
			participant_list = []
			for par in self.participants:
				row_list.append(par)

			options = self.get_program_session()
			for op in options[1:]:
				for rl in row_list:
					old_status = None
					if rl.attendance_data:
						att_data_list = ast.literal_eval(rl.attendance_data)
						if op in att_data_list:
							old_status = att_data_list[op]

					row = {
						"program_session": op,
						"employee":  rl.employee,
						"employee_name": rl.employee_name,
						"company": rl.company,
						"old_status": old_status,
						"new_status": rl.new_status,
						"row_name": rl.row_name,
						"attendance_data": rl.attendance_data,
					}
					participant_list.append(row)

			self.set('participants', [])
			for ue in participant_list:
				row = self.append('participants', {})
				row.update(ue)

	def save_attendance_changes(self):
		att_data_list = {}	
		status = None
		options = self.get_program_session()
		if self.program_session != "All":
			for d in self.participants:
				if d.new_status:
					if d.attendance_data:
						att_data_list = ast.literal_eval(d.attendance_data)

					status = ""
					att_data_list[d.program_session] = d.new_status
					for att in options[1:]:
						if att in att_data_list:
							status += "<b>"+cstr(att)+" : "+cstr(att_data_list[att])+"\n</b>"

					frappe.db.sql("""UPDATE `tabLearning Participants` SET `status` = %s, `attendance_data` = %s WHERE `name` = %s """,( status, cstr(att_data_list), d.row_name ))
					frappe.db.commit()
		else:
			for d in self.participants:
				if d.new_status:
					update_data = frappe.db.sql("""SELECT * FROM `tabLearning Participants` WHERE `name` = %s """, (d.row_name), as_dict=True)
					if update_data[0].attendance_data:
						att_data_list = ast.literal_eval(update_data[0].attendance_data)

					status = ""
					att_data_list[d.program_session] = d.new_status
					for att in options[1:]:
						if att in att_data_list:
							status += "<b>"+cstr(att)+" : "+cstr(att_data_list[att])+"\n</b>"

					frappe.db.sql("""UPDATE `tabLearning Participants` SET `status` = %s, `attendance_data` = %s WHERE `name` = %s """,( status, cstr(att_data_list), d.row_name ))
					frappe.db.commit()

	def create_evaluation_entries(self):
		eval_existing = {}
		eval_created = {}
		eval_template = frappe.db.sql(""" SELECT `parent` FROM `tabLearning Evaluation Template Table Apply For` WHERE `apply_for` = %s """, (self.learning_event), as_dict=True)
		if eval_template:
			eval_items = frappe.db.sql(""" SELECT `items_for_evaluation` FROM `tabLearning Evaluation Template Table` WHERE `parent` = %s ORDER BY `idx` ASC """, (eval_template[0].parent), as_dict=True)
			for d in self.participants:
				if d.new_status == "Present":
					exist = frappe.db.sql(""" SELECT `name` FROM `tabLearning Session Evaluation` WHERE `learning_event` = %s 
						AND `learning_session` = %s AND `rated_by` = %s """, (self.learning_event, d.program_session, d.employee), as_dict=True)
					if exist:
						if d.program_session not in eval_existing:
							eval_existing[d.program_session] = []
						eval_existing[d.program_session].append(cstr(d.employee)+": "+cstr(d.employee_name))
					else:
						eval_entry = frappe.new_doc("Evaluation for Learners")
						eval_entry.update({
							"event": self.learning_event,
							"program": d.program_session,
							"employee": d.employee,
							"comment": "None",
							"company": frappe.get_value("Employee", d.employee, "company"),
							"department": frappe.get_value("Employee", d.employee, "department"),
							"owner": frappe.get_value("Employee", d.employee, "user_id"),
						})

						for i in eval_items:                
							eval_entry.append('evaluation_table',{
								"items": i.items_for_evaluation,
								"rating": 0.00,
							})

						if eval_entry.insert():
							eval_entry.save()
							if d.program_session not in eval_created:
								eval_created[d.program_session] = []
							eval_created[d.program_session].append(cstr(d.employee)+": "+cstr(d.employee_name))

			if eval_created:
				for ses in eval_created:
					created_employees = ", <br>".join(str(x) for x in eval_created[ses])
					frappe.msgprint(_("{0}, Evaluation for Learners created for employee(s) <br> {1} ").format(ses, created_employees))

			if eval_existing:
				for prog in eval_existing:
					existing_employees = ", <br>".join(str(x) for x in eval_existing[prog])
					frappe.msgprint(_("{0}, Evaluation for Learners already exist for employee(s) <br> {1}").format(prog, existing_employees))
		else:
			frappe.msgprint(_("No Evaluation for Learners created"))

	def create_session_evaluation_entries(self):
		session_eval_existing = {}
		session_eval_created = {}
		session_eval_template = frappe.db.sql(""" SELECT `parent` FROM `tabLearning Evaluation Template Table Apply For` WHERE `apply_for` = %s """, (self.learning_event), as_dict=True)
		if session_eval_template:
			session_eval_items = frappe.db.sql(""" SELECT `items_for_evaluation` FROM `tabLearning Evaluation Template Table` WHERE `parent` = %s ORDER BY `idx` ASC """, (session_eval_template[0].parent), as_dict=True)
			for d in self.participants:
				if d.new_status == "Present":
					exist = frappe.db.sql(""" SELECT `name` FROM `tabLearning Session Evaluation` WHERE `learning_event` = %s 
						AND `learning_session` = %s AND `rated_by` = %s """, (self.learning_event, d.program_session, d.employee), as_dict=True)
					if exist:
						if d.program_session not in session_eval_existing:
							session_eval_existing[d.program_session] = []
						session_eval_existing[d.program_session].append(cstr(d.employee)+": "+cstr(d.employee_name))
					else:
						sesion_eval_entry = frappe.new_doc("Learning Session Evaluation")
						sesion_eval_entry.update({
							"learning_session": d.program_session,
							"learning_event": self.learning_event,
							"rated_by": d.employee,
							"rated_by_name": d.employee_name,
							"company": frappe.get_value("Employee", d.employee, "company"),
							"owner": frappe.get_value("Employee", d.employee, "user_id"),
						})

						for i in session_eval_items:                
							sesion_eval_entry.append('evaluation_table',{
								"items": i.items_for_evaluation,
								"rating": 0.00,
							})

						if sesion_eval_entry.insert():
							sesion_eval_entry.save()
							if d.program_session not in session_eval_created:
								session_eval_created[d.program_session] = []
							session_eval_created[d.program_session].append(cstr(d.employee)+": "+cstr(d.employee_name))

			if session_eval_created:
				for ses in session_eval_created:
					created_employees = ", <br>".join(str(x) for x in session_eval_created[ses])
					frappe.msgprint(_("{0}, Learning Session Evaluation created for <br> {1} ").format(ses, created_employees))

			if session_eval_existing:
				for prog in session_eval_existing:
					existing_employees = ", <br>".join(str(x) for x in session_eval_existing[prog])
					frappe.msgprint(_("{0}, Learning Session Evaluation already exist for <br> {1}").format(prog, existing_employees))
		else:
			frappe.msgprint(_("No Learning Session Evaluation created"))