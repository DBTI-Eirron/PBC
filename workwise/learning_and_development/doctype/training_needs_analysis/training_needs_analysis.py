# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate
from frappe import _
from frappe.model.document import Document

class TrainingNeedsAnalysis(Document):
	def validate(self):
		self.validate_fields()

	def on_submit(self):
		pass

	def validate_fields(self):
		if self.type == "Individual":
			if not self.employee:
				frappe.throw(_("Employee is required"))
		if self.type == "Department":
			if not self.department:
				frappe.throw(_("Department is required"))

	def get_sessions(self):
		self.set('session', [])
		program_sessions = frappe.db.sql(""" SELECT session, objective, methodology FROM `tabLearning Session Table` 
			WHERE `parent` = %s """,(self.training_name), as_dict=True)

		for a in program_sessions:
			i = {
				"session": a.session,
				"objective": a.objective,
				"methodology": a.methodology
			}

			self.append('session', i)

	def get_employees(self):
		self.set('participants', [])
		employees = frappe.db.sql(""" SELECT `name`, full_name, company, department FROM `tabEmployee` 
			WHERE is_active = 1 AND department = %s """,(self.department), as_dict=True)

		for a in employees:
			i = {
				"employee": a.name,
				"employee_name": a.full_name,
				"company": a.company,
				"department": a.department
			}

			self.append('participants', i)