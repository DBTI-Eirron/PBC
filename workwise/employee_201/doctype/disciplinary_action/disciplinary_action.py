# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, flt, getdate, cstr, add_to_date, get_datetime, nowdate
from frappe import throw,_
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.timekeeping_utils import chk_time_format, timediff_hrs, timediff_mins, datediff_days
from workwise.time_keeping.attendance_utils import get_actual_logs

class DisciplinaryAction(Document):
	def validate(self):
		self.validate_employee()

	def validate_employee(self):
		offenders = frappe.db.sql("""select employee from `tabInvolved Employees` 
			where parent=%s and involvement="Offender" and docstatus=1 """,(self.incident_report), as_dict=True)

		offender = 0
		for i in offenders:
			if i.employee == self.employee:
				offender = 1

		if offender == 0:
			throw(_("Employee is not an Offender"))

	def calc_days(self):
		self.suspension = int( (datediff_days(self.suspended_from, self.suspended_to, "%Y-%m-%d")).days + 1 )
		if self.ex_holiday or self.ex_restday:
			shift = get_actual_logs(self.employee, getdate(self.suspended_from), getdate(self.suspended_to))
			company = frappe.db.get_value("Employee", self.employee, ["company"] )

			holidays = frappe.db.sql("""SELECT holiday_name, holiday_date, is_special, location FROM `tabHoliday` 
				WHERE company = %s AND holiday_date >= %s AND holiday_date <= %s
				ORDER BY holiday_date ASC""",(company, getdate(self.suspended_from), getdate(self.suspended_to)), as_dict=True)


			for s in shift:
				if (s['is_restday'] and self.ex_restday):
					self.suspension = (int(self.suspension) - 1)
					continue
				if self.ex_holiday:
					for h in holidays:
						if s['target_date'] == h['holiday_date']:
							self.suspension = (int(self.suspension) - 1)
							continue


@frappe.whitelist()
def make_movement(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.movement_type = frappe.db.get_value("Sanction", source.sanction, "sanction")

	doc = get_mapped_doc("Disciplinary Action", source_name, {
			"Disciplinary Action": {
				"doctype": "Employee Movement",
				"field_map": {
					"sanction": "movement_type"
				}}
		}, target_doc, set_missing_values)
	return doc