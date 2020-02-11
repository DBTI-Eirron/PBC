# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.contacts.address_and_contact import load_address_and_contact, delete_contact_and_address
from frappe.model.document import Document

class Company(Document):
	
	def onload(self):
		load_address_and_contact(self, "company")

	def on_trash(self):
		delete_contact_and_address('Company', self.name)

	def on_update(self):
		if not frappe.db.exists("Cost Center",self.company_name):
			cost_center = frappe.new_doc("Cost Center")
			cost_center.update({
				"cost_center_name": self.company_name,
				"parent_cost_center": "Cost Center Structure",
				"is_group":1,
				"is_root":1,
				"company":self.company_name,
			})
			cost_center.save()

		if not frappe.db.exists("Department",self.company_name):
			department = frappe.new_doc("Department")
			department.update({
				"department_name": self.company_name,
				"parent_department": "Organizational Structure",
				"is_group":1,
				"is_root":1,
				"company":self.company_name,
			})
			department.save()

@frappe.whitelist()
def get_company_logo(user):
	emp = frappe.db.sql(""" SELECT `name`, `user_id` FROM `tabEmployee` WHERE user_id = %s AND user_id != "" AND user_id is not null LIMIT 1""",(user))
	if emp:
		emp = emp[0][0]
		company = frappe.db.get_value("Employee", emp, "company")
		new_logo = frappe.db.get_value("Company", company, "company_logo")
		if new_logo:
			return new_logo