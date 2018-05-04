# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint
from frappe import _

from frappe.model.document import Document

class AppraisalTemplate(Document):
	def validate(self):
		self.check_total_points()
		
	def check_total_points(self):	
		total_points = 0
		for d in self.get("goals"):
			total_points += int(d.weightage or 0)

		if cint(total_points) != 100:
			frappe.throw(_("Sum of points for all goals should be 100. It is {0}").format(total_points))