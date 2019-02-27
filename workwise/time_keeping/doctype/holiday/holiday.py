# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.model.naming import make_autoname
from frappe.model.document import Document

class Holiday(Document):
	pass
	#def validate(self):
	#	self.validate_holiday_req()
	#	self.validate_holiday()
	#
	#def validate_holiday(self):
	#	holidays = frappe.db.sql("""SELECT `name` FROM `tabHoliday`
	#		WHERE `name` != %s AND holiday_date = %s AND company = %s AND location = %s """, (self.name, self.holiday_date, self.company, self.location), as_dict=True)
	#	if holidays:
	#		frappe.throw(_("Holiday Already Exist"))
	#def validate_holiday_req(self):
	#	comp_only_holiday = frappe.db.get_single_value('Timekeeping Settings', 'comp_only_holiday')
	#	if not comp_only_holiday:
	#		if not self.location:
	#			frappe.throw("Location is Required")

