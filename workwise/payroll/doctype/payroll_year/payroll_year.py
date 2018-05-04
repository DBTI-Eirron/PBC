# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class PayrollYear(Document):
	def validate(self):
		self.validate_date()
		self.validate_range()

	def validate_date(self):
		if self.from_date > self.to_date:
			throw(_("To Date cannot be before From Date"))

	def validate_range(self):
		from_exist = frappe.db.sql("""SELECT `name` FROM `tabPayroll Year` WHERE `name`!= %s AND %s BETWEEN from_date AND to_date  """, (self.name, self.from_date) )
		to_exist = frappe.db.sql("""SELECT `name` FROM `tabPayroll Year` WHERE `name`!= %s AND %s BETWEEN from_date AND to_date """, (self.name, self.to_date) )
		if from_exist:
			frappe.throw(_("Payroll Year Already Exist for From Date"))
		if to_exist:
			frappe.throw(_("Payroll Year  Already Exist for To Date"))