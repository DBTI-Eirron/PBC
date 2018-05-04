# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class WorkScheduleTemplate(Document):
	def autoname(self):
		abbr = frappe.get_value("Company", self.company, "abbr")
		self.name = self.template_name + " - " + abbr
