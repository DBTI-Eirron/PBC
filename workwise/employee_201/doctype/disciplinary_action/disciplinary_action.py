# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe import throw,_
from workwise.time_keeping.timekeeping_utils import chk_time_format, timediff_hrs, timediff_mins, datediff_days

class DisciplinaryAction(Document):
	def validate(self):
		self.validate_employee()

	def validate_employee(self):
		offenders = frappe.db.sql("""select employee from `tabInvolved Employees` 
			where parent=%s and involvement="Offender" and docstatus=1 """,(self.incident_report), as_dict=True)

		offender = 0
		for i in offenders:
			if i.employee == self.employee:
				offender = 1

		if offender == 0:
			throw(_("Employee is not an Offender"))

	def calc_days(self):
		self.suspension = int( (datediff_days(self.suspended_from, self.suspended_to, "%Y-%m-%d")).days + 1 )

@frappe.whitelist()
def make_movement(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.movement_type = frappe.db.get_value("Sanction", source.sanction, "sanction")

	doc = get_mapped_doc("Disciplinary Action", source_name, {
			"Disciplinary Action": {
				"doctype": "Employee Movement",
				"field_map": {
					"sanction": "movement_type"
				}}
		}, target_doc, set_missing_values)
	return doc