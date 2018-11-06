# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint, throw
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, nowdate
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class BackgroundInvestigation(Document):
	def on_submit(self):
		self.update_applicant_status()

	def update_applicant_status(self):
		if self.investigation_status == "Passed":
			frappe.db.sql(""" Update `tabSchedules and Assessment` SET apply_type='Job Offer' where name=%s""", (self.schedule))
			self.db_set("apply_type", "Job Offer")
		elif self.investigation_status == "Failed":
			frappe.db.sql(""" Update `tabSchedules and Assessment` SET apply_type='Stopped' where name=%s""", (self.schedule))
			self.db_set("apply_type", "Stopped")

@frappe.whitelist()
def make_offer(source_name, target_doc=None):

	def update_target(source_doc, target_doc, source_parent):
		target_doc.job_applicant = source_doc.applicant
		target_doc.applicant_name = source_doc.applicant_name
		target_doc.offer_date = nowdate()

		applicant = frappe.db.sql(""" SELECT * FROM `tabJob Applicant` WHERE `name` = %s LIMIT 1""", source_doc.applicant, as_dict=1)
		
		for d in applicant:
			job_level, department = frappe.db.get_value("Position Title", d.apply_for, ["job_level","department"])
			head = frappe.db.get_value("Department", department, "head")
			head_name = frappe.db.get_value("Employee", head, "full_name")
			
			target_doc.position_title = d.apply_for
			target_doc.job_level = job_level
			target_doc.department_head = head
			target_doc.head_name = head_name

	doclist = get_mapped_doc("Background Investigation", source_name, {
		"Background Investigation": {
			"doctype": "Offer Letter",
			"validation": {
				"docstatus": ["=", 1]
			},
			"postprocess": update_target
		}
	}, target_doc)

	return doclist