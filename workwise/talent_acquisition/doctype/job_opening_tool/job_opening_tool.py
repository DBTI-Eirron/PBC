# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe import throw, _, scrub
from frappe.model.document import Document

class JobOpeningTool(Document):
	def validate(self):

		job_opening = frappe.get_doc("Job Opening", self.job_opening)
		job_opening.status = self.opening_status
		job_opening.save(ignore_permissions=True)
				#add_in_notice.update({
				#	"user_permission": new_user_perm.name
				#})
				#add_in_notice.save()

