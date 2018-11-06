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
			frappe.db.sql(""" Update `tabBackground Investigation` SET apply_type='For Contract Signing' where applicant=%s""", (self.job_applicant))
			self.db_set("apply_type", "For Contract Signing")
			if self.signed_contract:
				self.db_set("apply_type", "For 201")

		else:
			frappe.db.sql(""" Update `tabBackground Investigation` SET apply_type='Job Acceptance' where applicant=%s""", (self.job_applicant))
			self.db_set("apply_type", "For Acceptance")

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

@frappe.whitelist()
def make_contract(source_name, target_doc=None):

	def update_target(source_doc, target_doc, source_parent):
		target_doc.job_applicant = source_doc.applicant
		target_doc.applicant_name = source_doc.applicant_name
		target_doc.offer_date = nowdate()

		applicant = frappe.db.sql(""" SELECT * FROM `tabJob Applicant` WHERE `name` = %s LIMIT 1""", source_doc.applicant, as_dict=1)
		
		for d in applicant:
			job_level, department = frappe.db.get_value("Position Title", d.apply_for, ["job_level","department"])
			company = frappe.db.get_value("Talent Requisition", d.talent_requisition, "company")

			head = frappe.db.get_value("Department", department, "head")
			head_name = frappe.db.get_value("Employee", head, "full_name")

			target_doc.company = d.company
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