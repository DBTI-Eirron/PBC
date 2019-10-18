# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, cstr, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document
from workwise.time_keeping.application_utils import validate_inactive_employee

class LeaveBalanceSetup(Document):
	def validate(self):
		validate_inactive_employee(self)
		self.remove_duplicates()

	def remove_duplicates(self):
		unique = []
		entries = []
		for d in self.balance_schedules:
			unique_name = _(cstr(d.leave_type)+"-"+cstr(d.trigger_on))
			if unique_name not in unique:
				unique.append(unique_name)
				entries.append({
					"leave_type": d.leave_type,
					"trigger_on": d.trigger_on,
					"credits": d.credits
				});
			else:
				frappe.msgprint(_("Duplicate Schedule Removed {0} {1} ").format(d.leave_type, d.trigger_on))

		self.set('balance_schedules', [])
		for e in entries:
			row = self.append('balance_schedules', {})
			row.update(e)