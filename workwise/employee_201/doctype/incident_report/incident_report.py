# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import get_datetime, today, cstr
from frappe import throw, _, scrub
from frappe.model.document import Document

class IncidentReport(Document):
	
	def validate(self):
		self.validate_datetime()
		self.validate_memo()
		self.get_email_list()

	def on_submit(self):
		self.make_memo()

	def validate_datetime(self):
		if self.date_time_offense and get_datetime(self.date_time_offense) > get_datetime(today()):
			throw(_("Date and Time of Incident cannot be greater than today."))

	def make_memo(self):
		for d in self.involved_employees:
			new_memo = frappe.new_doc("Memo")
			new_memo.update({
				"employee": d.employee,
				"involvement": d.involvement,
				"department": d.department,
				"offense": self.offense,
			})

			new_memo.insert()

	def validate_memo(self):
		check_list = []
		for d in self.involved_employees:
			check_list.append(cstr(d.employee))

		unique_chk_list = set(check_list)
		if len(unique_chk_list) != len(check_list):
			throw(_("Same Employee has been entered multiple times"))

	def on_cancel(self):
		delete_list = frappe.db.sql("""SELECT `name`, `user_permission` FROM `tabNotice to Explain` WHERE incident_report =%s""", (self.name), as_dict=1)
		for dl in delete_list:
			frappe.delete_doc("User Permission", dl.user_permission)
			frappe.delete_doc("Notice to Explain",dl.name)

	def get_email_list(self):
		email_list = []
		for d in self.involved_employees:
			email = frappe.get_value("Employee", d.employee, "email")
			if email:
				email_list.append(email)

		if email_list:
			email_list = ', '.join(email_list)
			self.email_list = email_list

#@frappe.whitelist()
	def make_notice_to_explain(self):
		message_print = "" 
		for ie in self.involved_employees:
			employee_name = frappe.get_value("Employee", ie.employee, "full_name")
			make_notice = frappe.new_doc("Notice to Explain")
			make_notice.update({
				"incident_report": self.name,
				"employee": ie.employee,
				"offense": self.offense,
				"involvement": ie.involvement,
				"date_time_offense": self.date_time_offense,
				"incident_location": self.incident_location,
				"employee_name": employee_name, 
				"workflow_state": "Pending",
				"explanation" : ""
			})
			make_notice.insert()
			user_id = frappe.db.get_value("Employee", ie.employee, "user_id")
			new_user_perm = frappe.new_doc("User Permission")
			new_user_perm.update({
				"user" : user_id,
				"allow" : "Notice To Explain",
				"for_value" : make_notice.name
			})
			if new_user_perm.insert():
				add_in_notice = frappe.get_doc("Notice to Explain", make_notice.name)
				add_in_notice.update({
					"user_permission": new_user_perm.name
				})
				add_in_notice.save()
				ie.user_name = new_user_perm.name
			if message_print:
				message_print += ", "+make_notice.name
			else:
				message_print += make_notice.name
		return message_print

	def send_email(self):
		content = """<h2> """+self.name+"""</h2>
		<p>You are involed in this reported incident</p>"""
		for d in self.involved_employees:
			recipient = frappe.db.get_value("Employee", d.employee, "email")
			if recipient:
				frappe.sendmail(recipients=[recipient], sender="test@example.com",subject="Incident Reported", content=content)
