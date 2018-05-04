# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator

from frappe.modules import scrub, get_doctype_module
from frappe.model.document import Document

class JobOpening(WebsiteGenerator):
	website = frappe._dict(
		template = "templates/generators/job_opening.html",
		condition_field = "publish",
		page_title_field = "job_title",
	)

	def validate(self):
		if not self.route:
			self.route = frappe.scrub(self.job_title).replace('_', '-')

	def get_context(self, context):
		context.parents = [{'name': 'jobs', 'title': _('All Jobs') }]

def get_list_context(context):
	context.title = _("Jobs")
	context.introduction = _('Current Job Openings')