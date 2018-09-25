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
		self.validate_employment_status()

	def validate_range(self):
		from_exist = frappe.db.sql("""SELECT `name` FROM `tabLeave Balance` WHERE `name`!= %s AND employee = %s 
			AND leave_type = %s AND from_date >= %s <= to_date """, (self.name, self.employee, self.leave_type, self.from_date))

		to_exist = frappe.db.sql("""SELECT `name` FROM `tabLeave Balance` WHERE `name`!= %s AND employee = %s 
			AND leave_type = %s AND from_date >= %s <= to_date """, (self.name, self.employee, self.leave_type, self.to_date))

		if from_exist:
			frappe.throw(_("Leave Balance Already Exist for From Date"))

		if to_exist:
			frappe.throw(_("Leave Balance Already Exist for To Date"))

	def validate_employment_status(self):
		access_list = []
		employment_status = frappe.get_value("Employee", self.employee, ["employment_status"])

		allow_from_employment_status = frappe.db.sql(""" SELECT DISTINCT employment_status FROM `tabLeave Type Table` WHERE `parent` = %s """, (self.leave_type), as_dict=True)

		if allow_from_employment_status:
			for a in allow_from_employment_status:
				access_list.append(a.employment_status)

			if employment_status not in access_list:
				frappe.throw(_("Employement Status {0} is not allowed for {1}").format(employment_status ,self.leave_type))