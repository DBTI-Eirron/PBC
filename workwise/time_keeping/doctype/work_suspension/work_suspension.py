# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, math
from frappe import _
from frappe.utils import cint, cstr, flt, nowdate, add_days, getdate, fmt_money, get_datetime, add_to_date
from frappe.model.document import Document
from workwise.time_keeping.timekeeping_utils import chk_time_format

class WorkSuspension(Document):
	def validate(self):
		self.validate_time_format()
		self.get_suspension_range()
		self.validate_is_active()

	def validate_time_format(self):
		time_fds = ['from_time', 'to_time']
		for fd in time_fds:
			chk_time_format(str(self.get(fd)), "%H:%M:%S")

	def get_suspension_range(self):
		suspension_start = get_datetime( str(self.suspension_date)+" "+ str(self.from_time) )
		suspension_end = get_datetime( str(self.suspension_date)+" "+ str(self.to_time) )
		if suspension_end < suspension_start:
			suspension_end = get_datetime( str(add_days(self.suspension_date, 1))+" "+ str(self.to_time) )

		self.suspension_start = suspension_start
		self.suspension_end = suspension_end

	def get_employees(self):
		query = "SELECT `name`, `full_name` FROM `tabEmployee` WHERE is_active"
		if self.company:
			query = query + " AND company = '"+self.company+"'"
		if self.location:
			query = query + " AND location = '"+self.location+"'"
		if self.department:
			query = query + " AND department = '"+self.department+"'"

		employees = frappe.db.sql(query,as_dict=True)
		entries	= []
		for d in employees:
			row = {
				"employee": d.name,
				"employee_name": d.full_name,
				"is_active":is_active
			}
			entries.append(row);

		for d in entries:
			row = self.append('apply_to', {})
			row.update(d)

	def set_name(self):
		for d in self.apply_to:
			employee_name = frappe.get_value('Employee',d.employee,'full_name')
			d.employee_name = employee_name

	def validate_is_active(self):
		for d in self.apply_to:
			if frappe.get_value('Employee',d.employee,'is_active') == 0:
				frappe.throw(_("Employee "+d.employee+": "+d.employee_name+" is not active."))