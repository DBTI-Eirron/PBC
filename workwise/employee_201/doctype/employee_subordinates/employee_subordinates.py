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