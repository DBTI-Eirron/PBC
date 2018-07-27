# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import throw, _, scrub
from frappe.model.document import Document

class EmployeeSubordinates(Document):

	def validate(self):
		if self.employee:
			user_id = frappe.db.get_value("Employee", self.employee, "user_id")
			if user_id and self.get("subordinates"):
				frappe.db.sql("""DELETE FROM `tabUser Permission` WHERE allow = 'Employee' AND user = %s AND for_value != %s """, (user_id, self.employee), as_dict=1)

				for d in self.get("subordinates"):
					frappe.permissions.add_user_permission("Employee", d.subordinate, user_id)
			else:
				frappe.throw(_("This Employee has no User ID."))

	def on_trash(self):
		user_id = frappe.db.get_value("Employee", self.employee, "user_id")
		if user_id:
			frappe.db.sql("""DELETE FROM `tabUser Permission` WHERE allow = 'Employee' AND user = %s AND for_value != %s """, (user_id, self.employee), as_dict=1)

	def validate(self):
		self.remove_duplicates()	

	def remove_duplicates(self):
		unique_emp = []
		unique_entries = []
		for d in self.subordinates:
			if d.subordinate not in unique_emp:
				unique_emp.append(d.subordinate);

				i = {
					"subordinate": d.subordinate,
					"subordinate_name": d.subordinate_name,
				}	
				unique_entries.append(i);

		self.set('subordinates', [])
		for ue in unique_entries:
			row = self.append('subordinates', {})
			row.update(ue)

	def filter_add(self):
		cur_user = frappe.session.user
		if not self.company:
			frappe.throw(_("Company is Required"))

		if self.filter_value and self.filter_type:
			entries = []
			employees = ""
			if self.filter_type == 'Employee':
				if not "Administrator" in frappe.get_roles(cur_user):
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s  AND `name` = %(filter_value)s AND sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
												INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s) ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
						"user": frappe.session.user,
					}, as_dict=True)
				else:
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s  AND `name` = %(filter_value)s AND sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
												INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`) ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
					}, as_dict=True)
			elif self.filter_type == 'Department':
				if not "Administrator" in frappe.get_roles(cur_user):
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s  AND department = %(filter_value)s AND sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
												INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s) ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
						"user": frappe.session.user,
					}, as_dict=True)
				else:
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s  AND department = %(filter_value)s AND sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
												INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`) ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
					}, as_dict=True)
			elif self.filter_type == 'Location':
				if not "Administrator" in frappe.get_roles(cur_user):
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s  AND location = %(filter_value)s AND sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
												INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s) ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
					}, as_dict=True)
				else:
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s  AND location = %(filter_value)s AND sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
												INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`) ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
						"user": frappe.session.user,
					}, as_dict=True)
			
			if employees:
				for d in employees:
					row = {
						"subordinate": d.name,
						"subordinate_name": d.full_name,
					}
				
					entries.append(row);

				for d in entries:
					row = self.append('subordinates', {})
					row.update(d)
			else:
				frappe.throw(_(" You dont have access to this employee "))
		else:
			frappe.throw(_(" Input Filter Value and Filter Type "))

	def filter_reset(self):
		self.set('subordinates', [])