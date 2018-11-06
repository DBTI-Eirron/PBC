# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe	import _

class TargetSetting(Document):
	def validate(self):
		self.validate_weight()
		self.validate_appraisee()
		# self.validate_kra()

	def load_appraisee_info(self):
		parent = frappe.db.sql("""SELECT S.`parent`,E.position_title FROM `tabEmployee` E INNER JOIN `tabSubordinates` S ON S.subordinate = E.name WHERE E.name = %s LIMIT 1""",(self.appraisee),as_dict=True)
		for par in parent:
			self.immediate_supervisor = par.parent
			self.supervisor_job_title = par.position_title
			self.immediate_supervisor_name = frappe.get_value('Employee',par.parent,'full_name')

	def change_key_indicator(self):
		result = []
		for d in self.key_result_area:
			result.append(d.key_result_area)
		return result

	def validate_weight(self):
		total_w = 0.0
		for d in self.key_indicator:
			total_w += float(d.weight)
		if total_w != 100:
			frappe.throw(_("Total weightage assigned should be 100%. It is {0}").format(str(total_w) + "%"))

	def validate_appraisee(self):
		if self.type == "Individual":
			if self.appraisee is None:
				frappe.throw(_("Select Appraisee"))
		elif self.type == "Department":
			if self.department is None:
				frappe.throw(_("Select Department"))

	# def validate_kra(self):
	# 	total = total_ki = 0 
	# 	for d in self.key_result_area:
	# 		total += 1
	# 		for x in self.key_indicator:
	# 			if x.key_result_area == d.key_result_area:
	# 				total_ki += 1
	# 		if total_ki > 3:
	# 			frappe.throw(_("Key Indicator per Result Area must not be greater than 3"))
	# 	if total > 4:
	# 		frappe.throw(_("Key Result Area must not be greater than 4"))

