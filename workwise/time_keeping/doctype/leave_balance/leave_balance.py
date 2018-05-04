# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import msgprint, _
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, comma_or, get_fullname
from frappe.model.document import Document

class LeaveBalance(Document):
	def validate(self):
		self.validate_range()

	def validate_range(self):
		from_exist = frappe.db.sql("""SELECT `name` FROM `tabLeave Balance` WHERE `name`!= %s AND employee = %s 
			AND leave_type = %s AND from_date >= %s <= to_date """, (self.name, self.employee, self.leave_type, self.from_date))

		to_exist = frappe.db.sql("""SELECT `name` FROM `tabLeave Balance` WHERE `name`!= %s AND employee = %s 
			AND leave_type = %s AND from_date >= %s <= to_date """, (self.name, self.employee, self.leave_type, self.to_date))

		if from_exist:
			frappe.throw(_("Leave Balance Already Exist for From Date"))

		if to_exist:
			frappe.throw(_("Leave Balance Already Exist for To Date"))
