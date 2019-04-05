# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import throw, _, scrub
from frappe.model.document import Document

class SensitivityLevel(Document):
	def validate(self):
		self.assign_user_permissions()

	def assign_user_permissions(self):
		self.remove_all_permissions()
		for d in self.allowed_users:
			frappe.permissions.add_user_permission("Sensitivity Level", self.name, d.allow_user)
			frappe.cache().delete_value('user_permissions')

	def remove_all_permissions(self):
		perms = frappe.db.sql("""SELECT `name`, for_value, user FROM `tabUser Permission` 
			WHERE allow = 'Sensitivity Level' AND for_value = %s """, (self.name), as_dict=1)
		if perms:
			for d in perms:
				frappe.permissions.remove_user_permission("Sensitivity Level", self.name, d.user)
			frappe.cache().delete_value('user_permissions')


