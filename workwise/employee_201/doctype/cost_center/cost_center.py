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
		self.validate_group()
		self.update_company()

	def update_nsm_model(self):
		frappe.utils.nestedset.update_nsm(self)

	def on_update(self):
		self.update_nsm_model()

	def autoname(self):
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
		# direct = []
		# child = []
		# for cc in cc_dict:
		# 	if cc.parent == "Cost Center Structure":
		# 		direct.append({"name":cc.name,"lft":cc.lft,"rgt":cc.rgt})
		# 	elif cc.parent is not None:
		# 		child.append({"name":cc.name,"lft":cc.lft,"rgt":cc.rgt})

		# for cost in child:
		# 	for center in direct:
		# 		if center.lft <= cost.lft and center.rgt >= cost.rgt:
		# 			frappe.db.sql("""""")

@frappe.whitelist()
def create_root():
	frappe.db.sql("""INSERT INTO `tabCost Center` (cost_center_name, modified_by, owner, creation, modified, `name`, parent_cost_center, lft, rgt) 
		VALUES ('Cost Center Structure','Administrator','Administrator',NOW(),NOW(),'Cost Center Structure','', 1, 2) """)

@frappe.whitelist()
def rebuild_costcenter_tree():
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
