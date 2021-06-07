# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, inspect
from frappe.contacts.address_and_contact import load_address_and_contact, delete_contact_and_address
from frappe.model.document import Document
from workwise.employee_201.doctype.department.department import (reset_tree as dpt_reset_tree, create_root as dpt_create_root, create_root_entries 
	as dpt_create_root_entries, set_default_parent as dpt_set_default_parent, rebuild_department_tree as dpt_rebuild_department_tree)
from workwise.employee_201.doctype.cost_center.cost_center import( reset_tree as cc_reset_tree, create_root as cc_create_root, create_root_entries 
	as cc_create_root_entries, set_default_parent as cc_set_default_parent, rebuild_cost_center_tree as cc_rebuild_cost_center_tree )

class Company(Document):
	def onload(self):
		load_address_and_contact(self, "company")

	def on_trash(self):
		delete_contact_and_address('Company', self.name)

	def before_insert(self):
		self.validate_costcenter_origin_root()
		self.validate_department_origin_root()

	def after_insert(self):
		self.create_dafault_accounts()
		self.create_costcenter_root()
		self.create_department_root()

	def create_costcenter_root(self):
		if not frappe.db.exists("Cost Center", self.company_name):
			cost_center = frappe.new_doc("Cost Center")
			cost_center.update({
				"name": self.company_name,
				"cost_center_name": self.company_name,
				"parent_cost_center": "Cost Center Structure",
				"is_group": 1,
				"is_root": 1,
				"company": self.company_name,
			})
			cost_center.insert(ignore_permissions=True)

	def create_department_root(self):
		if not frappe.db.exists("Department", self.company_name):
			department = frappe.new_doc("Department")
			department.update({
				"name": self.company_name,
				"department_name": self.company_name,
				"parent_department": "Organizational Structure",
				"is_group": 1,
				"is_root": 1,
				"company": self.company_name,
			})
			department.insert(ignore_permissions=True)

	def validate_costcenter_origin_root(self):
		if not frappe.db.exists("Cost Center", "Cost Center Structure"):
			cc_reset_tree()
			cc_create_root()
			cc_create_root_entries()
			cc_set_default_parent()
			cc_rebuild_cost_center_tree()

	def validate_department_origin_root(self):
		if not frappe.db.exists("Department", "Organizational Structure"):
			dpt_reset_tree()
			dpt_create_root()
			dpt_create_root_entries()
			dpt_set_default_parent()
			dpt_rebuild_department_tree()

	def create_dafault_accounts(self):
		default_account_roots = [
			{'account_number': '1000000', 'account_name': 'Asset'},
			{'account_number': '2000000', 'account_name': 'Liability'},
			{'account_number': '3000000', 'account_name': 'Equity'},
			{'account_number': '4000000', 'account_name': 'Income'},
			{'account_number': '5000000', 'account_name': 'Expense'},
		]

		for def_acnt in default_account_roots:
			def_acnt['account'] = str(def_acnt['account_number'])+" - "+str(def_acnt['account_name'])+" - "+str(self.abbr)
			if not frappe.db.exists("Account", def_acnt['account']):
				new_account = frappe.new_doc("Account")
				new_account.update({
					"account_name": def_acnt['account_name'],
					"account_number": def_acnt['account_number'],
					"root_type": def_acnt['account_name'],
					"report_type": "Balance Sheet",
					"is_group": 1,
					"company": self.company_name,
				})
				new_account.insert(ignore_permissions=True, ignore_mandatory=True)

@frappe.whitelist()
def get_company_logo(user):
	emp = frappe.db.sql(""" SELECT `name`, `user_id` FROM `tabEmployee` WHERE user_id = %s AND user_id != "" AND user_id is not null LIMIT 1""",(user))
	if emp:
		emp = emp[0][0]
		company = frappe.db.get_value("Employee", emp, "company")
		new_logo = frappe.db.get_value("Company", company, "company_logo")
		if new_logo:
			return new_logo