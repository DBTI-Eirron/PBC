# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate, getdate
from frappe.model.document import Document
from workwise.time_keeping.application_utils import (grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, 
validate_reject_cancel_own_application, change_owner, get_levelled_approval, get_levelled_approval_rejection, validate_inactive_employee)

class ChangeRequestApplication(Document):
	def validate(self):
		validate_inactive_employee(self)
		self.get_request()
		self.validate_item_format()
		grant_head_subordinate_access(self)
		change_owner(self)
		self.validate_civil_status()

	def on_submit(self):
		validate_approve_own_application(self)
		get_approver_and_date(self)
		self.approve_request()

	def before_update_after_submit(self):
		get_levelled_approval(self)
		self.validate_civil_status()

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		doc = frappe.get_doc("Change Request Application", self.name)
		if doc.docstatus == 2:
			for item_req in self.get("change_request"):
				item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Employee" AND `label`=%s """, (item_req.item), as_dict=True)
				for item in item_sel:
					if item_req.action == "Approved":
						frappe.client.set_value("Employee", self.employee, item.fieldname, item_req.current)

	def get_request(self):
		for item_req in self.change_request:
			item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Employee" AND `label`=%s """, (item_req.item), as_dict=True)
			for item in item_sel:
				item_cur = frappe.db.get_value("Employee", self.employee, item.fieldname)
				item_req.current = item_cur

	def validate_item_format(self):
		for item_req in self.change_request:
			if item_req.item == "Birthday":
				item_req.request = getdate(item_req.request)

	def approve_request(self):
		for item_req in self.get("change_request"):
			item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Employee" AND `label`=%s """, (item_req.item), as_dict=True)
			for item in item_sel:
				item_cur = frappe.db.get_value("Employee", self.employee, item.fieldname)
				item_req.current = item_cur
				
				if item_req.action == "Approved":
					frappe.client.set_value("Employee", self.employee, item.fieldname, item_req.request)

	def validate_civil_status(self):
		validate = 0
		for item_req in self.get("change_request"):
			if item_req.item == "Civil Status" and item_req.current == "Single":
				for i in self.get("change_request"):
					if i.item == "Spouse" and i.request != "":
						frappe.db.set_value("Employee", self.employee, "spouse", "None")
						validate = 1
				if validate == 0:
					frappe.throw(_("Spouse is required if Married"))
					