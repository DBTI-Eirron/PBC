# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import msgprint, _
from frappe.model.naming import make_autoname
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, comma_or, get_fullname, nowdate, getdate
from frappe.model.document import Document

class PayrollPeriod(Document):
	def autoname(self):
		pay_year = getdate(self.payroll_date).strftime("%Y")

		from_year = getdate(self.from_date).strftime("%Y")
		from_month = getdate(self.from_date).strftime("%b")
		from_day = getdate(self.from_date).strftime("%d")

		to_year = getdate(self.to_date).strftime("%Y")
		to_month = getdate(self.to_date).strftime("%b")
		to_day = getdate(self.to_date).strftime("%d")

		abbr = frappe.get_value("Company", self.company, "abbr")
		self.name = from_month+""+from_day+" "+to_month+""+to_day+" - "+abbr+pay_year

	def validate(self):
		self.validate_days()
		self.validate_frequency()

	def validate_frequency(self):
		if self.schedule == "Monthly":
			self.frequency = "2nd"
			frappe.msgprint("Frequency Changed to ( 2nd ) because Schedule was set to Monthly")

	def validate_days(self):
		difference = date_diff(self.to_date, self.from_date)
		if self.schedule == "Monthly":
			if not difference > 27:
				frappe.throw(_("Monthly Schedule Should be Greater than {0} days ").format(difference))
		if difference > 31:
			frappe.throw("Days Should not be Greater than 31 days ")