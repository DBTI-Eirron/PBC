# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.naming import make_autoname
from frappe.model.document import Document

class Location(Document):
	def validate(self):
		self.validate_location()

	def autoname(self):
		abbr = frappe.db.get_value("Company", self.company, "abbr")
		self.name = self.location_name+" - "+abbr

	def validate_location(self):
		holidays = frappe.db.sql("""SELECT `name` FROM `tabLocation`
			WHERE `name` != %s AND company = %s AND location_name = %s """, (self.name, self.company, self.location_name), as_dict=True)
		if holidays:
			frappe.throw(_("Location Already Exist"))