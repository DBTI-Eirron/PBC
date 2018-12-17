# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate
from frappe.model.document import Document
from workwise.time_keeping.application_utils import grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, change_owner

class ExcuseTardinessApplication(Document):
	def validate(self):
		grant_head_subordinate_access(self)
		change_owner(self)

	def on_submit(self):
		time_in, time_out = self.get_timelogs()
		if not time_in and not time_out:
			frappe.throw(("No timelogs for employee"))
		validate_approve_own_application(self)
		get_approver_and_date(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)

	def load_timecard(self):
		time_in, time_out = self.get_timelogs()
		if time_in:
			self.to_time = time_in[0].time
		if time_out:
			self.from_time = time_out[0].time

	def get_timelogs(self):
		bio_id = frappe.get_value("Employee", self.employee, "biometrics_id")
		if bio_id:
			time_out = frappe.db.sql(""" SELECT `time` FROM `tabTime Card` WHERE `biometrics_id` = %s AND `card_type` = 0 AND `is_disabled` = 0 AND `date` = %s LIMIT 1 """, (bio_id, self.date), as_dict=True)
			time_in = frappe.db.sql(""" SELECT `time` FROM `tabTime Card` WHERE `biometrics_id` = %s AND `card_type` = 1 AND `is_disabled` = 0 AND `date` = %s LIMIT 1 """, (bio_id, self.date), as_dict=True)

			return time_in, time_out