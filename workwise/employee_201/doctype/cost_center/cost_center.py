# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, validate_email_add
from frappe import throw, _
from frappe.utils.nestedset import NestedSet, rebuild_tree

class CostCenter(NestedSet):
	nsm_parent_field = 'parent_cost_center'

	def validate(self):
		self.validate_company()
		self.validate_group()
		self.update_company()

	def validate_company(self):
		if not self.company:
			frappe.throw("Please Create Cost Center in Cost Center Tree.")

	def update_nsm_model(self):
		frappe.utils.nestedset.update_nsm(self)

	def on_update(self):
		self.update_nsm_model()

	def autoname(self):
		if self.parent_cost_center != 'Cost Center Structure' and self.company:
			abbr = frappe.db.get_value("Company", self.company, "abbr")
			self.name = self.cost_center_name+" - "+abbr

	def on_trash(self):
		self.update_nsm_model()

	def validate_group(self):
		if not self.is_group:
			if not self.parent_cost_center:
				frappe.throw("Parent Cost Center is Required if not group")

	def update_company(self):
		cc_dict = frappe.db.sql("""SELECT `name`, lft, rgt, parent FROM `tabCost Center` WHERE parent_cost_center = 'Cost Center Structure'""",as_dict=True)
		for cc in cc_dict:
			if cc.lft <= self.lft and cc.rgt >= self.rgt:
				self.company = cc.name

@frappe.whitelist()
def reset_tree():
	frappe.db.sql("""UPDATE `tabCost Center` SET lft=NULL, rgt=NULL """)

@frappe.whitelist()
def create_root():
	cost_center_root = frappe.db.sql("""SELECT `name` FROM `tabCost Center` WHERE `name`='Cost Center Structure' """, as_list=True)
	if cost_center_root:
		frappe.db.sql("""DELETE FROM `tabCost Center` WHERE `name` = 'Cost Center Structure' """)

	frappe.db.sql("""INSERT INTO `tabCost Center` (cost_center_name, modified_by, owner, creation, modified, `name`, parent_cost_center, lft, rgt, is_root) 
		VALUES ('Cost Center Structure','Administrator','Administrator',NOW(),NOW(),'Cost Center Structure','', 1, 2, 1) """)

@frappe.whitelist()
def create_root_entries():
	company = frappe.db.sql("""SELECT `name` FROM `tabCompany` """, as_dict=True)
	cost_center = frappe.db.sql("""SELECT `name` FROM `tabCost Center` """, as_list=True)
	for com in company:
		frappe.db.sql("""DELETE FROM `tabCost Center` WHERE `name` = '{0}' """.format(com.name))

		if com not in cost_center:
			frappe.db.sql("""INSERT INTO `tabCost Center` (cost_center_name, modified_by, owner, creation, modified, `name`, parent_cost_center, is_root, is_group) 
				VALUES ('{0}', 'Administrator', 'Administrator', NOW(), NOW(), '{0}','Cost Center Structure', 1, 1) """.format(com.name))

@frappe.whitelist()
def set_default_parent():
	frappe.db.sql("""UPDATE `tabCost Center` SET parent_cost_center='Cost Center Structure' WHERE parent_cost_center IS NULL """)

@frappe.whitelist()
def company_as_parent_cost_center():
	frappe.db.sql("""UPDATE `tabCost Center` SET parent_cost_center=company WHERE company IN (SELECT `name` FROM `tabCompany`) """)

@frappe.whitelist()
def parent_cost_center_as_company():
	frappe.db.sql("""UPDATE `tabCost Center` SET company=parent_cost_center WHERE parent_cost_center IN (SELECT `name` FROM `tabCompany`) """)

@frappe.whitelist()
def rename_cost_center():
	import frappe.model.rename_doc as rd

	company = frappe.db.sql("""SELECT `name` FROM `tabCompany` """, as_dict=True)
	excluded_list = ['Cost Center Structure', 'Cost Center Tree']
	for com in company:
		excluded_list.append(cstr(com.name))
	excluded_str = "', '".join(excluded_list)
	excluded_str = "'"+excluded_str+"'"

	frappe.db.sql("""UPDATE `tabCost Center` TD LEFT JOIN `tabCompany` TC ON TD.`company`=TC.`name` SET TD.`cost_center_name`=TRIM(CONCAT(" - ", TC.abbr) FROM TD.`name`) """)
	dept_list = frappe.db.sql(""" SELECT TD.`name`, TD.`cost_center_name`, TD.`company`, TC.`abbr` FROM `tabCost Center` TD LEFT JOIN `tabCompany` TC ON TD.`company`=TC.`name` WHERE TD.`company` IN ({0}) """.format(excluded_str), as_dict=1)
	for dept in dept_list:
		rd.rename_doc("Cost Center", dept.name, cstr(dept.cost_center_name)+" - "+cstr(dept.abbr), force=True)

@frappe.whitelist()
def rebuild_cost_center_tree():
	rebuild_tree("Cost Center", "parent_cost_center")

@frappe.whitelist()
def get_children(doctype, parent=None, is_root=False):
	if is_root:
		parent = ""

	costcenters = frappe.db.sql("""
		select 
			name as value, 
			cost_center_name as title,
			is_group as expandable
		from
			`tabCost Center` emp
		where 
		ifnull(`parent_cost_center`,'') = %s order by name""", parent, as_dict=1)

	return costcenters

@frappe.whitelist()
def add_node():
	from frappe.desk.treeview import make_tree_args
	args = make_tree_args(**frappe.form_dict)

	if cint(args.is_root):
		args.parent_cost_center = None

	frappe.get_doc(args).insert()
