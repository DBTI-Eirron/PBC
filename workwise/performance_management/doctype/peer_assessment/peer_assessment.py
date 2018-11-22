# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class PeerAssessment(Document):
	def validate(self):
		self.validate_assignment()
		self.create_forms()

	def create_forms(self):
		self.delete_forms()
		for emp in self.assignment:
			self.create_base(emp)
		self.fill_table()

	def fill_table(self):
		new_forms = frappe.db.sql("""SELECT `name`,`creation`,`modified`,`modified_by` FROM`tabPeer Assessment Form` WHERE `parent` = %s""",(self.name),as_dict=True)
		for form in new_forms:
			for items in self.values_indicator:
				header = {
					"parent":form.name,
					"parentfield":"values_indicator",
					"parenttype":"Peer Assessment Form",
					"idx":items.idx,
					"values_indicator":items.values_indicator,
					"docstatus":0,
					"creation":form.creation,
					"modified":form.modified,
					"modified_by":form.modified_by
				}
				pr = frappe.new_doc("Peer Assessment Form Table")
				pr.update(header)
				pr.insert()
				# frappe.db.sql("""INSERT INTO `tabPeer Assessment Form Table` (parent,parentfield,parenttype,idx,values_indicator,docstatus,creation,modified,modified_by)
				# VALUES (%s,"values_indicator","Peer Assessment Form",%s,%s,0,%s,%s,%s);
				# """,(form.name,items.idx,items.values_indicator,form.creation,form.modified,form.modified_by),as_dict=True)
				# frappe.db.commit()
	def create_base(self,emp):
		full_name = frappe.get_value("Employee",emp.assign_to,"full_name")
		header = {
			"appraisee":self.appraisee,
			"appraisee_name":self.appraisee_name,
			"dpartment":self.department,
			"position":self.position,
			"period_covered":self.period_covered,
			"description":self.description,
			"assigned_to":full_name,
			"assigned":emp.assign_to,
			"parent":self.name,
			"owner":emp.assign_to
		}
		pr = frappe.new_doc("Peer Assessment Form")
		pr.update(header)
		pr.insert()

	def delete_forms(self):
		frappe.db.sql("""DELETE FROM `tabPeer Assessment Form` WHERE parent= %s""",(self.name), as_dict=1)

	def validate_assignment(self):
		total_assignment = 0
		for ass in self.assignment:
			total_assignment += 1
		if total_assignment < 1:
			frappe.throw("Add Assign to.")

	def display_settings_value(self):
		entries = []
		description = frappe.db.get_single_value('Peer Assessment Settings', 'description')
		self.description = description
		indicators = frappe.db.sql("""SELECT values_indicator FROM `tabPeer Assessment Settings Table`""",as_dict=True)
		for d in indicators:
			row = {
				"values_indicator": d.values_indicator,
			}
			entries.append(row);

		for d in entries:
			row = self.append('values_indicator', {})
			row.update(d)
