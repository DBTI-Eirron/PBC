# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate
from frappe.model.document import Document

class DTRProblemApplication(Document):
	def validate(self):
		self.get_request()

	def on_submit(self):
		self.approve_request()
		self.get_approver_and_date()

	def on_cancel(self):
		self.revert_request()

	def get_request(self):
		for req in self.get("time_record_request"):
			card = self.get_card_type(req)
			timecard_sel = self.get_timecard(card)
			for a in timecard_sel:
				req.current = frappe.db.get_value("Time Card", a.name, "time")

	def approve_request(self):
		for req in self.get("time_record_request"):
			if req.action == "Approved":
				card = self.get_card_type(req)
				timecard_sel = self.get_timecard(card)
				frappe.client.set_value("Time Card", timecard_sel[0].name, "time", req.request)

	def revert_request(self):
		for req in self.get("time_record_request"):
			if req.action == "Approved":
				card = self.get_card_type(req)
				timecard_sel = self.get_timecard(card)
				frappe.client.set_value("Time Card", timecard_sel[0].name, "time", req.current)

	def get_card_type(self, req):
		if req.type == "Time In":
			card_type = 0
		if req.type == "Time Out":
			card_type = 1
		if req.type == "Break In":
			card_type = 2
		if req.type == "Break Out":
			card_type = 3

		return card_type

	def get_timecard(self, card):
		timecard_sel = frappe.db.sql("""SELECT TC.`name` FROM `tabTime Card` TC JOIN `tabEmployee` TE WHERE TC.biometrics_id = TE.biometrics_id  AND TC.`date` = %s AND TC.`card_type` = %s AND TE.`name` = %s LIMIT 1 """, (self.target_date, card, self.employee), as_dict=True)

		return timecard_sel

	def get_approver_and_date(self):
		self.approved_by = frappe.session.user
		self.date_approved = nowdate()
