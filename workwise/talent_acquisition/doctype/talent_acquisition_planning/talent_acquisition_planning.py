# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, nowdate
from frappe.model.document import Document

class TalentAcquisitionPlanning(Document):

	def validate(self):
		self.validate_duplicate_position()
		#self.validate_exist()
		self.calculate_totals()	

	def on_submit(self):
		self.create_tr()

	def validate_duplicate_position(self):
		unique = []
		for d in self.positions:
			if d.position not in unique:
				unique.append(d.position);
			else:
				frappe.throw(_("Duplicate Position on Row {0}, {1} ").format(d.idx ,d.position ))

	def validate_exist(self):
		exist = frappe.db.sql(""" SELECT `name` FROM `tabTalent Acquisition Planning` WHERE `name` != %s AND department = %s AND payroll_year = %s  """, (self.name, self.department, self.payroll_year), as_dict=1)
		if exist:
			for d in exist:
				frappe.throw(_("Duplicate Talent Acquisition Planning, {0} Already Exists ").format(d.name))

	def calculate_totals(self):
		budget_amount = 0.0
		for d in self.positions:
			budget_amount += d.amount

		self.budget_amount = budget_amount

	def create_tr(self):
		for d in self.positions:
			job_level = frappe.db.get_value("Postion Title", d.position, "job_level")
			job_function = frappe.db.sql(""" SELECT `description` FROM `tabPosition Job Function` WHERE `parent` = %s """, d.position, as_dict=1)
			technical_requirement = frappe.db.sql(""" SELECT `description` FROM `tabPosition Technical Requirement` WHERE `parent` = %s  """, d.position, as_dict=1)
			attitude_requirement = frappe.db.sql(""" SELECT `description` FROM `tabPosition Attitude Requirement` WHERE `parent` = %s  """, d.position, as_dict=1)
			optional_qualification = frappe.db.sql(""" SELECT `description` FROM `tabPosition Optional Qualification` WHERE `parent` = %s """, d.position, as_dict=1)

			tr = frappe.new_doc("Talent Requisition")
			tr.update({
				"company": self.company,
				"department": self.department,
				"talent_source": "Internal",
				"nature": "Budgeted",
				"requested_on": nowdate(),
				"completed_on": "",
				"date_needed": "",
				"position_title": d.position,
				"job_level": job_level,
				"employment_status": "Probationary",
				"quantity": d.qty,
				"rate_type": "Monthly Rate",
				"min_salary": 0,
				"max_salary": d.rate,
			})

			for d in job_function:
				tr.append("job_function", {
					"description": d.description,
				})

			for d in technical_requirement:
				tr.append("technical_requirement", {
					"description": d.description,
				})

			for d in attitude_requirement:
				tr.append("attitude_requirement", {
					"description": d.description,
				})

			for d in optional_qualification:
				tr.append("optional_qualification", {
					"description": d.description,
				})

			tr.insert()