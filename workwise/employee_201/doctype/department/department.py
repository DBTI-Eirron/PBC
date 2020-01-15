# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, validate_email_add
from frappe import throw, _
from frappe.utils.nestedset import NestedSet, rebuild_tree

class Department(NestedSet):
	nsm_parent_field = 'parent_department'

	def validate(self):
		self.validate_group()
		self.validate_department()

	def update_nsm_model(self):
		frappe.utils.nestedset.update_nsm(self)

	def on_update(self):
		self.update_nsm_model()

	def on_trash(self):
		self.update_nsm_model()

	def validate_group(self):
		if not self.is_group:
			if not self.parent_department:
				frappe.throw("Parent Department is Required if not group")

	def autoname(self):
		abbr = frappe.db.get_value("Company", self.company, "abbr")
		self.name = self.department_name+" - "+abbr

	def validate_department(self):
		holidays = frappe.db.sql("""SELECT `name` FROM `tabDepartment`
			WHERE `name` != %s AND company = %s AND department_name = %s """, (self.name, self.company, self.department_name), as_dict=True)
		if holidays:
			frappe.throw(_("Department Already Exist"))

@frappe.whitelist()
def add_node():
	from frappe.desk.treeview import make_tree_args
	args = make_tree_args(**frappe.form_dict)

	if cint(args.is_root):
		args.parent_department = None

	frappe.get_doc(args).insert()

@frappe.whitelist()
def create_root():
	department_root = frappe.db.sql("""SELECT `name` FROM `tabDepartment` WHERE `name`='Organizational Structure' """, as_list=True)
	if department_root:
		frappe.db.sql("""DELETE FROM `tabDepartment` WHERE `name` = 'Organizational Structure' """)

	frappe.db.sql("""INSERT INTO `tabDepartment` (department_name, modified_by, owner, creation, modified, `name`, parent_department, lft, rgt, is_root) 
		VALUES ('Organizational Structure','Administrator','Administrator',NOW(),NOW(),'Organizational Structure','', 1, 2, 1) """)

@frappe.whitelist()
def create_root_entries():
	company = frappe.db.sql("""SELECT `name` FROM `tabCompany` """, as_dict=True)
	department = frappe.db.sql("""SELECT `name` FROM `tabDepartment` """, as_list=True)
	for com in company:
		frappe.db.sql("""DELETE FROM `tabDepartment` WHERE `name` = '{0}' """.format(com.name))

		if com not in department:
			frappe.db.sql("""INSERT INTO `tabDepartment` (department_name, modified_by, owner, creation, modified, `name`, parent_department, is_root, is_group) 
				VALUES ('{0}', 'Administrator', 'Administrator', NOW(), NOW(), '{0}','Organizational Structure', 1, 1) """.format(com.name))

@frappe.whitelist()
def update_parent_department_as_company():
	frappe.db.sql("""UPDATE `tabDepartment` SET parent_department=company WHERE parent_department IS NULL AND is_root = 0 """)

@frappe.whitelist()
def rebuild_department_tree():
	rebuild_tree("Department", "parent_department")

@frappe.whitelist()
def get_children(doctype, parent=None, is_root=False):
	if is_root:
		parent = ""

	departments = frappe.db.sql("""
		select 
			name as value, 
			department_name as title,
			is_group as expandable
		from
			`tabDepartment` emp
		where 
		ifnull(`parent_department`,'') = %s order by name""", parent, as_dict=1)

	return departments