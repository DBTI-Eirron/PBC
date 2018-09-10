# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import timedelta, datetime
from frappe import _
from frappe.utils import nowdate, cstr, getdate
from frappe.model.document import Document

class DTRProblemApplication(Document):
	def validate(self):
		self.get_request()
		
	def on_submit(self):
		self.approve_request()
		self.get_approver_details()

	def on_cancel(self):
		self.revert_request()

	def get_request(self):
		for req in self.get("time_record_request"):
			card = self.get_card_type(req)
			timecard_sel = self.get_timecard(card)
			for a in timecard_sel:
				req.current = frappe.db.get_value("Time Card", a.name, "time")
				req.time_card = frappe.db.get_value("Time Card", a.name)

	def approve_request(self):
		for req in self.get("time_record_request"):
			if req.action == "Approved" and req.current:
				card = self.get_card_type(req)
				timecard_sel = self.get_timecard(card)
				frappe.client.set_value("Time Card", timecard_sel[0].name, "time", req.request)
			if req.action == "Approved" and not req.current:
				self.make_timecard()

	def revert_request(self):
		for req in self.get("time_record_request"):
			if req.action == "Approved" and req.current:
				card = self.get_card_type(req)
				timecard_sel = self.get_timecard(card)
				frappe.client.set_value("Time Card", timecard_sel[0].name, "time", req.current)
			if req.action == "Approved" and not req.current:
				if req.time_card:
					if frappe.db.exists("Time Card", req.time_card):
						frappe.delete_doc("Time Card", req.time_card)
				else:
					dtr_date = self.update_target_date()
					bio = frappe.db.get_value("Employee", self.employee, "biometrics_id")
					card = self.get_card_type(req)
					frappe.db.sql(""" DELETE FROM `tabTime Card` WHERE `biometrics_id` = %s AND card_type = %s AND `date` = %s AND `time` = %s """, (bio, card, dtr_date, req.request), as_dict=True)
					frappe.db.commit()

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

	def get_approver_details(self):
		self.approved_by = frappe.session.user
		self.approved_on = nowdate()

	def update_target_date(self):
		target_date = datetime.strptime(str(self.target_date) + ' ' + '00:00:00', '%Y-%m-%d %H:%M:%S').date()
		#frappe.throw(_(target_date))
		if self.is_previous:
			target_date = target_date - timedelta(days=1)
		else:
			target_date = self.target_date

		return target_date

	def make_timecard(self):
		target_date = self.update_target_date()
		bio = frappe.db.get_value("Employee", self.employee, "biometrics_id")
		for req in self.get("time_record_request"):
			card_type = self.get_card_type(req)
			new_timecard = frappe.new_doc("Time Card")
			new_timecard.update({
				"biometrics_id": bio,
				"card_type": card_type,
				"date": str(target_date),
				"time": req.request
			})

			new_timecard.insert()
			new_timecard.save()