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

@frappe.whitelist()
def get_company_logo(user):
	emp = frappe.db.sql(""" SELECT `name`, `user_id` FROM `tabEmployee` WHERE user_id = %s AND user_id != "" AND user_id is not null LIMIT 1""",(user))
	if emp:
		emp = emp[0][0]
		company = frappe.db.get_value("Employee", emp, "company")
		new_logo = frappe.db.get_value("Company", company, "company_logo")
		if new_logo:
			return new_logo