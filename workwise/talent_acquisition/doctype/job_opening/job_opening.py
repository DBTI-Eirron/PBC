# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator

from frappe.modules import scrub, get_doctype_module
from frappe.model.document import Document

class JobOpening(Document):
	def on_submit(self):
		tool = frappe.db.get_value("Job Opening Tool", self.position_title, "name")
		if tool:
			frappe.db.sql(""" UPDATE `tabJob Opening Tool` SET opening_status = 'Open' WHERE position_title = %s """, self.position_title, as_dict=1)

		else:
			jot = frappe.new_doc("Job Opening Tool")
			jot.update({
				"position_title": self.position_title,
				"job_opening": self.name,
				"status": "Open",
			})
			jot.insert()