# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate
from frappe.model.document import Document

class ChangeRequestApplication(Document):
	def validate(self):
		self.get_request()

	def on_submit(self):
		self.approve_request()
		self.get_approver_and_date()

	def on_cancel(self):
		doc = frappe.get_doc("Change Request Application", self.name)
		if doc.docstatus == 2:
			for item_req in self.get("change_request"):
				item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Employee" AND `label`=%s """, (item_req.item), as_dict=True)
				for item in item_sel:
					if item_req.action == "Approved":
						frappe.client.set_value("Employee", self.employee, item.fieldname, item_req.current)

	def get_request(self):
		for item_req in self.get("change_request"):
			item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Employee" AND `label`=%s """, (item_req.item), as_dict=True)
			for item in item_sel:
				item_cur = frappe.db.get_value("Employee", self.employee, item.fieldname)
				item_req.current = item_cur

	def approve_request(self):
		for item_req in self.get("change_request"):
			item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Employee" AND `label`=%s """, (item_req.item), as_dict=True)
			for item in item_sel:
				item_cur = frappe.db.get_value("Employee", self.employee, item.fieldname)
				item_req.current = item_cur

				if item_req.action == "Approved":
					frappe.client.set_value("Employee", self.employee, item.fieldname, item_req.request)

	def get_approver_and_date(self):
		self.approved_by = frappe.session.user
		self.date_approved = nowdate()