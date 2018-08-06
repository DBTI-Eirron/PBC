# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate
from frappe.model.document import Document

class ExcuseTardinessApplication(Document):
	def validate(self):
		pass

	def on_submit(self):
		self.get_approver_and_date()

	def on_cancel(self):
		pass

	def get_approver_and_date(self):
		self.approved_by = frappe.session.user
		self.approved_on = nowdate()

	def load_timecard(self):
		bio_id = frappe.get_value("Employee", self.employee, "biometrics_id")
		if bio_id:
			time_in = frappe.db.sql(""" SELECT `time` FROM `tabTime Card` WHERE `biometrics_id` = %s AND `card_type` = 1 AND `is_disabled` = 0 AND `date` = %s LIMIT 1 """, (bio_id, self.date), as_dict=True)
			if time_in:
				self.to_time = time_in[0].time
			time_out = frappe.db.sql(""" SELECT `time` FROM `tabTime Card` WHERE `biometrics_id` = %s AND `card_type` = 0 AND `is_disabled` = 0 AND `date` = %s LIMIT 1 """, (bio_id, self.date), as_dict=True)
			if time_out:
				self.from_time = time_in[0].time