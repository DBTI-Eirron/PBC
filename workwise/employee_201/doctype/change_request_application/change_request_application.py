# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate, getdate
from frappe.model.document import Document
from workwise.time_keeping.application_utils import (grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, get_employee_details,
validate_reject_cancel_own_application, change_owner, get_levelled_approval, get_levelled_approval_rejection, validate_inactive_employee)

class ChangeRequestApplication(Document):
	def validate(self):
		get_employee_details(self)
		validate_inactive_employee(self)
		if self.item_category == "Other":
			self.get_request()
			self.validate_item_format()
			self.validate_civil_status()
		if self.item_category == "Address":
			self.get_request_address()
		if self.item_category == "Contact":
			self.get_request_contact()
		grant_head_subordinate_access(self)
		change_owner(self)		

	def on_submit(self):
		validate_approve_own_application(self)
		get_approver_and_date(self)
		if self.item_category == "Other":
			self.approve_request()
		if self.item_category == "Address":
			self.approve_request_address()
		if self.item_category == "Contact":
			self.approve_request_contact()

	def before_update_after_submit(self):
		get_levelled_approval(self)
		if self.item_category == "Other":
			self.validate_civil_status()

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		doc = frappe.get_doc("Change Request Application", self.name)
		if doc.docstatus == 2:
			if self.item_category == "Other":
				self.cancel_request()
			if self.item_category == "Address":
				self.cancel_request_address()
			if self.item_category == "Contact":
				self.cancel_request_contact()

	def cancel_request(self):
		for item_req in self.get("change_request"):
			item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Employee" AND `label`=%s """, (item_req.item), as_dict=True)
			for item in item_sel:
				if item_req.action == "Approved":
					frappe.db.set_value("Employee", self.employee, item.fieldname, item_req.current)

	def cancel_request_address(self):
		for item_req in self.get("change_request_address"):
			item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Address" AND `label`=%s """, (item_req.item), as_dict=True)
			for item in item_sel:
				if item_req.action == "Approved":
					frappe.db.set_value("Address", item_req.address, item.fieldname, item_req.current)

	def cancel_request_contact(self):
		for item_req in self.get("change_request_contact"):
			item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Contact" AND `label`=%s """, (item_req.item), as_dict=True)
			for item in item_sel:
				if item_req.action == "Approved":
					frappe.db.set_value("Employee", item_req.contact, item.fieldname, item_req.current)

	def get_request(self):
		for item_req in self.change_request:
			if item_req.item:
				item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Employee" AND `label`=%s """, (item_req.item), as_dict=True)
				for item in item_sel:
					item_cur = frappe.db.get_value("Employee", self.employee, item.fieldname)
					item_req.current = item_cur

	def get_request_address(self):
		for item_req in self.change_request_address:
			if item_req.item and item_req.address:
				item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Address" AND `label`=%s """, (item_req.item), as_dict=True)
				for item in item_sel:
					item_cur = frappe.db.get_value("Address", item_req.address, item.fieldname)
					item_req.current = item_cur

	def get_request_contact(self):
		for item_req in self.change_request_contact:
			if item_req.item and item_req.contact:
				item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Contact" AND `label`=%s """, (item_req.item), as_dict=True)
				for item in item_sel:
					item_cur = frappe.db.get_value("Contact", item_req.contact, item.fieldname)
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
					frappe.db.set_value("Employee", self.employee, item.fieldname, item_req.request)

	def approve_request_address(self):
		for item_req in self.get("change_request_address"):
			item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Address" AND `label`=%s """, (item_req.item), as_dict=True)
			for item in item_sel:
				item_cur = frappe.db.get_value("Address", item_req.address, item.fieldname)
				item_req.current = item_cur
				
				if item_req.action == "Approved":
					frappe.db.set_value("Address", item_req.address, item.fieldname, item_req.request)

	def approve_request_contact(self):
		for item_req in self.get("change_request_contact"):
			item_sel = frappe.db.sql("""SELECT fieldname FROM `tabDocField` WHERE `parent`="Contact" AND `label`=%s """, (item_req.item), as_dict=True)
			for item in item_sel:
				item_cur = frappe.db.get_value("Contact", item_req.contact, item.fieldname)
				item_req.current = item_cur
				
				if item_req.action == "Approved":
					frappe.db.set_value("Contact", item_req.contact, item.fieldname, item_req.request)

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
	
	def get_employee_address(self):
		if self.employee and self.item_category == "Address":
			result = []
			address_list = frappe.get_all("Dynamic Link", filters={"link_doctype": "Employee", "link_name": self.employee, "parenttype": "Address"}, fields=["parent"])
			for address in address_list:
				result.append(str(address.parent))

			return result

	def get_employee_contact(self):
		if self.employee and self.item_category == "Contact":
			result = []
			contact_list = frappe.get_all("Dynamic Link", filters={"link_doctype": "Employee", "link_name": self.employee, "parenttype": "Contact"}, fields=["parent"])
			for contact in contact_list:
				result.append(str(contact.parent))

			return result