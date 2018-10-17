# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import throw, _, scrub
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class OfferLetter(Document):
	def on_update_after_submit(self):
		if self.status == "Accepted":
			frappe.db.sql(""" Update `tabInterview and Background` SET apply_type='For 201' where applicant=%s""", (self.job_applicant))
			self.db_set("apply_type", "For 201")
		else:
			frappe.db.sql(""" Update `tabInterview and Background` SET apply_type='Job Offer' where applicant=%s""", (self.job_applicant))
			self.db_set("apply_type", "")

@frappe.whitelist()
def get_name(source_name, source_value):
	if source_name == "Applicant":
		target_name = frappe.db.get_value("Job Applicant", source_value, "applicant_name");
		target_job_opening = frappe.db.get_value("Job Applicant", source_value, "apply_for");
		target_company = frappe.db.get_value("Job Applicant", source_value, "company");
		target_location = frappe.db.get_value("Job Applicant", source_value, "location");
		

	fields_list = {
		"target_name": target_name,
		"target_job_opening": target_job_opening,
		"target_company": target_company,
		"target_location": target_location,
	}

	return fields_list

@frappe.whitelist()
def make_employee(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.first_name, target.last_name, target.middle_name, target.email_address = frappe.db.get_value("Job Applicant", source.job_applicant, ["first_name", "last_name", "middle_name", "email_address"])
		target.job_offer = source.name

	doc = get_mapped_doc("Offer Letter", source_name, {
			"Offer Letter": {
				"doctype": "Employee",
				"field_map": {
					"applicant_name": "full_name",
				}}

		}, target_doc, set_missing_values)

	return doc