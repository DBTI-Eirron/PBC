# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import timedelta, datetime
from frappe import _
from frappe.utils import nowdate, cstr, getdate
from frappe.model.document import Document
from workwise.time_keeping.application_utils import grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, change_owner, get_levelled_approval, get_levelled_approval_rejection

class DTRProblemApplication(Document):
	def validate(self):
		self.validate_application()
		self.get_timekeeping_settings()
		grant_head_subordinate_access(self)
		self.get_request()
		change_owner(self)
		
	def on_submit(self):
		validate_approve_own_application(self)
		self.approve_request()
		get_approver_and_date(self)

	def before_update_after_submit(self):
		get_levelled_approval(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		self.revert_request()

	def validate_application(self):
		if datetime.strptime(str(self.target_date), '%Y-%m-%d').date() > datetime.strptime(str(nowdate()), '%Y-%m-%d').date():
			frappe.throw(_("<b>DTR Problem Application: {0}</b><hr> You cannot file in advance for DTR Problem Application").format(self.name))

	def get_timekeeping_settings(self):
		cur_month = datetime.strptime(str(self.target_date), '%Y-%m-%d').month
		cur_year = datetime.strptime(str(self.target_date), '%Y-%m-%d').year
		max_month = frappe.db.get_single_value('Timekeeping Settings', 'dtrp_max_monthly')
		max_year = frappe.db.get_single_value('Timekeeping Settings', 'dtrp_max_yearly')

		dtrp_record_month = frappe.db.sql("""SELECT count(`name`) as count FROM `tabDTR Problem Application` 
			WHERE docstatus = 1 AND employee = %s AND company = %s AND MONTH(`target_date`) = %s AND YEAR(`target_date`) = %s """, (self.employee, self.company, cur_month, cur_year), as_dict=True)
		if dtrp_record_month:
			if max_month != 0:
				if int(dtrp_record_month[0].count) > int(max_month):
					frappe.throw(_("<b>DTR Problem Application: {0}</b><hr> You have reached the maximum number of filing per month").format(self.name))

		dtrp_record_year = frappe.db.sql("""SELECT count(`name`) as count FROM `tabDTR Problem Application` 
			WHERE docstatus = 1 AND employee = %s AND company = %s AND YEAR(`target_date`) = %s """, (self.employee, self.company, cur_year), as_dict=True)
		if dtrp_record_year:
			if max_year != 0:
				if int(dtrp_record_year[0].count) > int(max_year):
					frappe.throw(_("<b>DTR Problem Application: {0}</b><hr> You have reached the maximum number of filing per year").format(self.name))

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
				if timecard_sel:
					for a in timecard_sel:
						frappe.client.set_value("Time Card", a.name, "time", req.request)
				else:
					self.make_timecard(req)
			if req.action == "Approved" and not req.current:
				self.make_timecard(req)

	def revert_request(self):
		for req in self.get("time_record_request"):
			if req.action == "Approved" and req.current:
				card = self.get_card_type(req)
				timecard_sel = self.get_timecard(card)
				if timecard_sel:
					for a in timecard_sel:
						frappe.client.set_value("Time Card", a.name, "time", req.current)
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

	def update_target_date(self):
		target_date = datetime.strptime(str(self.target_date) + ' ' + '00:00:00', '%Y-%m-%d %H:%M:%S').date()
		#frappe.throw(_(target_date))
		if self.is_previous:
			target_date = target_date - timedelta(days=1)
		else:
			target_date = self.target_date

		return target_date

	def make_timecard(self, req):
		target_date = self.update_target_date()
		bio = frappe.db.get_value("Employee", self.employee, "biometrics_id")

		card_type = self.get_card_type(req)
		new_timecard = frappe.new_doc("Time Card")
		new_timecard.update({
			"biometrics_id": bio,
			"card_type": card_type,
			"date": str(target_date),
			"time": str(req.request)
		})

		new_timecard.insert()
		new_timecard.save()