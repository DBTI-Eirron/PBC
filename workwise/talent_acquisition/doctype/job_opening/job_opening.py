# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator

from frappe.modules import scrub, get_doctype_module
from frappe.model.document import Document

class JobOpening(Document):
	pass