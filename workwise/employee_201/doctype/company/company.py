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