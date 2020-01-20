# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, validate_email_add, cstr
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
def employee_dept_for_company():
	frappe.db.sql("""UPDATE `tabEmployee` TE 
		INNER JOIN `tabCompany` C  ON TE.`company`=C.`name`
		SET TE.`department`=CONCAT(TE.`department`, " - ", C.abbr) WHERE TE.department IS NOT NULL """)

@frappe.whitelist()
def clone_dept_for_company():
	company = frappe.db.sql("""SELECT `name`, abbr FROM `tabCompany` """, as_dict=True)
	excluded_list = ['Organizational Structure', 'Department Tree']
	for com in company:
		excluded_list.append(cstr(com.name))
	excluded_str = "', '".join(excluded_list)
	excluded_str = "'"+excluded_str+"'"
	departments = frappe.db.sql("""SELECT D.`name`, D.`department_name`, C.`abbr`, C.`name` as company FROM `tabDepartment` D INNER JOIN `tabCompany` C ON D.`company`=C.`name` WHERE D.`name` NOT IN ({0}) """.format(excluded_str), as_dict=True)
	dept_list = []
	existing_list = []
	for dep in departments:
		dept_list.append(dep.department_name)
		existing_list.append(dep.name)

	for cm in company:
		for dp in dept_list:
			if cstr(dp)+" - "+cstr(cm.abbr) not in existing_list:
				new_dept = frappe.new_doc("Department")
				new_dept.update({
					"company": cm.name,
					"department_name": dp,
					"parent_department": cm.name,
				})
				new_dept.flags.ignore_permissions = True
				new_dept.save()

@frappe.whitelist()
def reset_tree():
	frappe.db.sql("""UPDATE `tabDepartment` SET lft=NULL, rgt=NULL """)

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
def set_default_parent():
	frappe.db.sql("""UPDATE `tabDepartment` SET parent_department='Organizational Structure' WHERE parent_department IS NULL """)

@frappe.whitelist()
def company_as_parent_department():
	frappe.db.sql("""UPDATE `tabDepartment` SET parent_department=company WHERE company IN (SELECT `name` FROM `tabCompany`) """)

@frappe.whitelist()
def parent_department_as_company():
	frappe.db.sql("""UPDATE `tabDepartment` SET company=parent_department WHERE parent_department IN (SELECT `name` FROM `tabCompany`) """)

@frappe.whitelist()
def rename_department():
	import frappe.model.rename_doc as rd

	company = frappe.db.sql("""SELECT `name` FROM `tabCompany` """, as_dict=True)
	excluded_list = ['Organizational Structure', 'Department Tree']
	for com in company:
		excluded_list.append(cstr(com.name))
	excluded_str = "', '".join(excluded_list)
	excluded_str = "'"+excluded_str+"'"

	frappe.db.sql("""UPDATE `tabDepartment` TD LEFT JOIN `tabCompany` TC ON TD.`company`=TC.`name` SET TD.`department_name`=TRIM(CONCAT(" - ", TC.abbr) FROM TD.`name`) """)
	dept_list = frappe.db.sql(""" SELECT TD.`name`, TD.`department_name`, TD.`company`, TC.`abbr` FROM `tabDepartment` TD LEFT JOIN `tabCompany` TC ON TD.`company`=TC.`name` WHERE TD.`company` IN ({0}) """.format(excluded_str), as_dict=1)
	for dept in dept_list:
		rd.rename_doc("Department", dept.name, cstr(dept.department_name)+" - "+cstr(dept.abbr), force=True)

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