# -*- coding: utf-8 -*-	
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint, throw
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, nowdate
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class SchedulesandAssessment(Document):
	def validate(self):
		self.get_department_head()

	def on_submit(self):
		self.update_applicant_status()

	def get_department_head(self):
		if not self.interviewer:
			department = frappe.db.get_value("Position Title", self.apply_for, "department")
			if department:
				head = frappe.db.get_value("Department", department, "head")

			if head:
				self.interviewer = head
				self.interviewer_name = frappe.db.get_value("Employee", head, "full_name")
			else:
				frappe.throw("Please Setup Head for {0}".format(self.apply_for))

	def update_applicant_status(self):
		frappe.db.sql(""" Update `tabJob Applicant` SET apply_type='For Interview', interview_date = %s where name = %s""", (self.scheduled_date, self.applicant))
		self.db_set("apply_type", "For Interview")

@frappe.whitelist()
def make_interview(source_name, target_doc=None):
	def add_entries(source, target):
		entries = []
		target.set("interview_result", [])
		template = frappe.db.sql(""" SELECT *  FROM `tabPosition Interview Template` WHERE `parent` = %s ORDER BY idx """, source.apply_for, as_dict=1)
		for d in template:
			info = { 
				"title": d.title,
				"category": d.category,
				"percentage": d.percentage,
				"score": 1
			}
			entries.append(info)

		for d in entries:
			row = target.append('interview_result', {})
			row.update(d)

	def update_target(source_doc, target_doc, source_parent):
		target_doc.applicant = source_doc.applicant
		target_doc.applicant_name = source_doc.applicant_name
		target_doc.schedule = source_doc.name
	
		target_doc.interviewer = source_doc.interviewer
		target_doc.interviewer_name = source_doc.interviewer_name
	
		target_doc.scheduled_date = source_doc.scheduled_date
		
		target_doc.interview_date = source_doc.interview_date
		target_doc.interview_status = source_doc.interview_status

	doclist = get_mapped_doc("Schedules and Assessment", source_name, {
		"Schedules and Assessment": {
			"doctype": "Interview",
			"validation": {
				"docstatus": ["=", 1]
			},
			"postprocess": update_target
		}
	}, target_doc, add_entries)

	return doclist

@frappe.whitelist()
def make_investigation(source_name, target_doc=None):
	def add_entries(source, target):
		entries = []
		target.set("investigation_result", [])
		template = frappe.db.sql(""" SELECT *  FROM `tabPosition Investigation Template` WHERE `parent` = %s ORDER BY idx """, source.apply_for, as_dict=1)
		for d in template:
			info = {
				"question": d.question,
			}
			entries.append(info)

		for d in entries:
			row = target.append('investigation_result', {})
			row.update(d)

	def update_target(source_doc, target_doc, source_parent):
		target_doc.applicant = source_doc.applicant
		target_doc.applicant_name = source_doc.applicant_name
		target_doc.schedule = source_doc.name	
		target_doc.investigation_date = nowdate()

	doclist = get_mapped_doc("Schedules and Assessment", source_name, {
		"Schedules and Assessment": {
			"doctype": "Background Investigation",
			"validation": {
				"docstatus": ["=", 1]
			},
			"postprocess": update_target
		}
	}, target_doc, add_entries)

	return doclist