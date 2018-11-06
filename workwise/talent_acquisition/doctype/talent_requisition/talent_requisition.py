# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, nowdate
from frappe.model.document import Document

class TalentRequisition(Document):
	def on_submit(self):
		self.create_job_opening()
		self.create_job_opening_tool()

	def create_job_opening(self):
		head = frappe.db.get_value("Department", self.department, "head")
		head_name = frappe.db.get_value("Employee", head, "full_name") if head else ""

		jo = frappe.new_doc("Job Opening")
		jo.update({
			"requisition": self.name,
			"department": self.department,
			"department_head": head,
			"head_name": head_name,
			"position_title": self.position_title,
			"posting_date": nowdate(),
			"status": "Open",
		})

		jo.insert()

	def create_job_opening_tool(self):
		tool = frappe.db.get_value("Job Opening Tool", self.position_title, "name")
		if tool:
			frappe.db.sql(""" UPDATE `tabJob Opening Tool` SET opening_status = 'Open' WHERE position_title = %s """, self.position_title, as_dict=1)

		else:
			jot = frappe.new_doc("Job Opening Tool")
			jot.update({
				"position_title": self.position_title,
				"status": "Open",
			})
			jot.insert()
			