# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class TargetSettings(Document):
	def validate(self):
		self.validate_weight()
		self.set_header()
		# self.validate_kra()

	def validate_weight(self):
		total_w = 0.0
		for d in self.key_indicator:
			total_w += float(d.weight)
		if total_w != 100:
			frappe.throw(_("Total weightage assigned should be 100%. It is {0}").format(str(total_w) + "%"))

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

