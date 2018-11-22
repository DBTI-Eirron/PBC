# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RatingClassification(Document):
	def validate(self):
		self.validate_rating()

	def validate_rating(self):
		pass
		# ratings = frappe.db.sql("""SELECT `name`, `rate_from`, `rate_to` FROM""",as_dict=True)
		# for d in ratings:
		# 	if self.rate_from <= d.rate_to and self.rate_from >= d.rate_from:
		# 		frappe.throw()
		# 	elif