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
				self.remove_all_permissions()
				for d in self.get("subordinates"):
					exists = frappe.db.sql(""" SELECT `name`, for_value FROM `tabUser Permission` WHERE `allow` = 'Employee' AND `user` = %s AND `for_value` = %s  """, (user_id, d.subordinate), as_dict=1)
					if not exists:
						user_perm = frappe.new_doc("User Permission")
						user_perm.update({
							"allow": "Employee",
							"for_value": d.subordinate,
							"user": user_id,
							"apply_for_all_roles": 0,
							"is_automated": 1
						})	
						user_perm.insert()
						frappe.db.commit()
						#frappe.permissions.add_user_permission("Employee", d.subordinate, user_id, 0, 1)
				frappe.cache().delete_value('user_permissions')
			else:
				frappe.throw(_("Employee {0} has no User ID.").format(self.employee))

	def remove_all_permissions(self):
		user_id = frappe.db.get_value("Employee", self.employee, "user_id")
		if user_id:
			perms = frappe.db.sql("""SELECT `name`, `for_value`, `is_automated` FROM `tabUser Permission` WHERE allow = 'Employee' AND `user` = %s AND for_value != %s """, (user_id, self.employee), as_dict=1)
			if perms:
				for d in perms:
					if d.is_automated > 0:
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
					lft, rgt = frappe.db.get_value("Department", self.filter_value, ["lft", "rgt"])
					employees = frappe.db.sql("""SELECT TE.`name`, TE.`full_name` FROM `tabEmployee` TE 
						LEFT JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name` 
						WHERE TE.company = %(company)s 
						AND ( DEPT.`lft` BETWEEN %(lft)s AND %(rgt)s ) ORDER BY TE.last_name, TE.first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
						"lft": lft,
						"rgt": rgt,
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