# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.model.naming import make_autoname
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, comma_or, get_fullname, nowdate, getdate
from frappe.model.document import Document

class WeeklySet(Document):
	def autoname(self):
		abbr = frappe.get_value("Company", self.company, "abbr")
		if not self.period_group:
			self.name = self.month+""+cstr(self.payroll_year)+" - "+abbr
		else:
			self.name = self.month+""+cstr(self.payroll_year)+" - "+abbr+"-"+cstr(self.period_group)

	def validate(self):
		self.get_month_number()

	def get_month_number(self):
		month_lib = {
			"Jan": 1,
			"Feb": 2,
			"Mar": 3,
			"Apr": 4,
			"May": 5,
			"Jun": 6,
			"Jul": 7,
			"Aug": 8,
			"Sep": 9,
			"Oct": 10,
			"Nov": 11,
			"Dec": 12,
		}
		self.month_number = month_lib[self.month]
