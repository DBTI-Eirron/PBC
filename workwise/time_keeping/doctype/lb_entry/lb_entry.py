# -*- coding: utf-8 -*-
# Copyright (c) 2019, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, math, calendar
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from frappe.utils import cint, cstr, flt, nowdate, add_days, getdate, fmt_money, get_datetime, add_to_date
from frappe import _
from frappe.model.document import Document

class LBEntry(Document):
	def validate(self):
		if self.balance_type == 'Less':
			deduct_to = frappe.db.get_value("Leave Type", self.leave_type, "deduct_to")
			self.deduct_credits_to = deduct_to if deduct_to else self.leave_type
		else:
			self.deduct_credits_to = None

		create = 1
		is_active, gender, civil_status, is_solo_parent, employment_status = frappe.db.get_value("Employee", self.employee, ["is_active", "gender", "civil_status", "is_solo_parent", "employment_status"])
		is_carry_over, female_only, male_only, married_only, solo_parent_only = frappe.db.get_value("Leave Type", self.leave_type, ["is_carry_over", "female_only", "male_only", "married_only", "solo_parent_only"])
		employment_status_setup = frappe.db.sql(""" SELECT employment_status FROM `tabLeave Type Table` WHERE `parent` = %s """,(self.leave_type), as_dict=1)
		employment_status_list = []
		for es in employment_status_setup:
			employment_status_list.append(es.employment_status)

		#Validate
		if female_only:
			if gender != "Female":
				create = 0

		if male_only:
			if gender != "Male":
				create = 0

		if married_only:
			if civil_status != "Married":
				create = 0

		if solo_parent_only: 
			if not is_solo_parent:
				create = 0

		if employment_status_list:
			if employment_status not in employment_status_list:
				create = 0

		if not create:
			frappe.throw(_('Leave Type requirements does not meet'))

		if not is_active:
			frappe.throw(_('Employee is not active'))

	def after_insert(self):
		if self.balance_type == "Add":
			self.deduct_add_lbentry_to_overused()

	def deduct_add_lbentry_to_overused(self):
		total_add_credit = abs(self.credits)
		overused_list = frappe.get_all("Overused LB Entry", filters={"employee": self.employee, "leave_type": self.deduct_credits_to, "status": "Pending"}, fields=["name"])
		for overused in overused_list:
			if total_add_credit > 0:
				total_remaining_credit = 0
				total_deduction_credit = total_add_credit
				doc = frappe.get_doc("Overused LB Entry", overused.name)
				total_remaining_credit = flt(doc.remaining_overused_credits)
				if total_remaining_credit < total_add_credit:
					total_deduction_credit = total_add_credit - total_remaining_credit
				doc.append('deduction_history', {
						"lb_entry": self.name,
						"credits": total_deduction_credit
					})
				doc.flags.ignore_permissions = True
				doc.save()