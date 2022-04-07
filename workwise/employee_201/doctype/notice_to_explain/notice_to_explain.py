# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import throw, _, scrub

class NoticetoExplain(Document):
	def on_submit(self):
		if not self.report_on:
			frappe.throw(_("Report On is Mandatory"))
		if not self.report_to:
			frappe.throw(_("Report To is Mandatory"))
