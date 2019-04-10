# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import throw, _, scrub
from frappe.model.document import Document

class EmployeeSubordinates(Document):
	def validate(self):
		self.remove_duplicates()	
		if self.employee:
			user_id = frappe.db.get_value("Employee", self.employee, "user_id")
			if user_id:
				for d in self.get("subordinates"):
					exists = frappe.db.sql(""" SELECT `name`, for_value FROM `tabUser Permission` WHERE `allow` = 'Employee' AND `user` = %s AND `for_value` = %s  """, (user_id, d.subordinate), as_dict=1)
					if not exists:
						frappe.permissions.add_user_permission("Employee", d.subordinate, user_id)
				frappe.cache().delete_value('user_permissions')
			else:
				frappe.throw(_("Employee {0} has no User ID.").format(self.employee))

	def remove_all_permissions(self):
		user_id = frappe.db.get_value("Employee", self.employee, "user_id")
		if user_id:
			perms = frappe.db.sql("""SELECT `name`, for_value FROM `tabUser Permission` WHERE allow = 'Employee' AND `user` = %s AND for_value != %s """, (user_id, self.employee), as_dict=1)
			if perms:
				for d in perms:
					frappe.permissions.remove_user_permission("Employee", d.for_value, user_id)
				frappe.cache().delete_value('user_permissions')
		else:
			frappe.throw(_("Employee {0} has no User ID.").format(self.employee))

	def on_trash(self):
		self.remove_all_permissions()

	def remove_duplicates(self):
		unique_emp = []
		unique_entries = []
		for d in self.subordinates:
			if d.subordinate not in unique_emp:
				unique_emp.append(d.subordinate);

				i = {
					"subordinate": d.subordinate,
					"subordinate_name": d.subordinate_name,
					"created_from_employee": d.created_from_employee,
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
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s AND `name` = %(filter_value)s ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
					}, as_dict=True)
			elif self.filter_type == 'Department':
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s AND department = %(filter_value)s ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
					}, as_dict=True)
			elif self.filter_type == 'Location':
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s AND location = %(filter_value)s ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
					}, as_dict=True)
			
			if employees:
				for d in employees:
					row = {
						"subordinate": d.name,
						"subordinate_name": d.full_name,
						"created_from_employee": d.created_from_employee,
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