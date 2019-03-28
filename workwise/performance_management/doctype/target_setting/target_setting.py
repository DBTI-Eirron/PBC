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
		self.set_header()
		# self.validate_kra()

	def load_appraisee_info(self):
		parent = frappe.db.sql("""SELECT S.`parent`,E.position_title FROM `tabEmployee` E INNER JOIN `tabSubordinates` S ON S.subordinate = E.name WHERE E.name = %s LIMIT 1""",(self.appraisee),as_dict=True)
		for par in parent:
			self.immediate_supervisor = par.parent
			self.supervisor_job_title = par.position_title
			self.immediate_supervisor_name = frappe.get_value('Employee',par.parent,'full_name')
		return self.type

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
				
	def get_type(self):
		return self.type

	def set_header(self):
		header = "STANDARDS:"
		result = frappe.db.sql("""SELECT rating_equivalent,rate_to FROM `tabRating Classification` ORDER BY rate_to ASC""",as_dict=True)
		for r in result:
			header += " " + str(int(r.rate_to)) + " - " + str(r.rating_equivalent) + " ,"
		header = header[:-1] + "."
		self.header = header

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

