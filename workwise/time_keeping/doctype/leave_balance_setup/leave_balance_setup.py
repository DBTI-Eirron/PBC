# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, cstr, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document

class LeaveBalanceSetup(Document):
	def validate(self):
		self.validate_table()
		self.validate_rows()

	def validate_table(self):
		unique = []
		entries = []
		for d in self.balance_schedules:
			unique_name = (cstr(d.leave_type)+"-"+cstr(d.method)+"-"+cstr(d.allocation_start)+"-"+cstr(d.method_condition)+"-"+cstr(d.value))
			if unique_name not in unique:
				unique.append(unique_name)
				entries.append({
					'leave_type': d.leave_type,
					'method': d.method,
					'allocation_start': d.allocation_start,
					'method_condition': d.method_condition,
					'value': d.value,
					'from_value': d.from_value,
					'to_value': d.to_value,
					'credits': d.credits,
					'add_from_movement': d.add_from_movement,
					'is_continuous': d.is_continuous,
					'end_type': d.end_type,
					'by_count_value': d.by_count_value,
					'by_end_of_year': d.by_end_of_year,
				});

		self.set('balance_schedules', [])
		for e in entries:
			row = self.append('balance_schedules', {})
			row.update(e)

	def validate_rows(self):
		for d in self.balance_schedules:
			if d.allocation_start in ['Date Hired in Years', 'Regularization in Years']:
				if not d.method_condition or not d.value:
					frappe.throw(_("Must have Method Condition and Method Value for Date Hired in Years or Regularization in Years"))

			if not d.allocation_start or d.allocation_start == 'Regular':
				if d.method_condition or d.value:
					frappe.throw(_("Must not have Method Condition and Method Value for Regular or Calendar"))



