# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import datetime
from frappe import _
from frappe.utils import nowdate, get_time, flt, add_days, get_datetime
from frappe.model.document import Document
from workwise.time_keeping.application_utils import ( grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, change_owner, get_levelled_approval, 
	get_levelled_approval_rejection, clear_approval_history, validate_inactive_employee, get_approver_email_list, get_cancelled_by_and_date, validate_approver_userperm, validate_cutoff_approval_date, get_employee_details )

class UndertimeApplication(Document):
	def validate(self):
		get_employee_details(self)
		validate_inactive_employee(self)
		clear_approval_history(self)
		grant_head_subordinate_access(self)
		change_owner(self)
		self.get_targetdate()
		self.get_totalhours()

	def on_submit(self):
		validate_approve_own_application(self)
		get_approver_and_date(self)
		get_approver_email_list(self, 'on_submit')
		#validate_approver_userperm(self)
		validate_cutoff_approval_date(self)

	def on_update(self):
		validate_reject_cancel_own_application(self)

	def before_update_after_submit(self):
		get_approver_email_list(self, 'before_update_after_submit')
		get_levelled_approval(self)
		#validate_approver_userperm(self)
		validate_cutoff_approval_date(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		get_cancelled_by_and_date(self)

	def get_targetdate(self):
		self.target_date = self.from_date
		if self.is_previous:
			self.target_date = add_days(self.from_date, - 1)

	def get_totalhours(self):
		#Get Total Hours
		from_datetime = get_datetime( str(self.from_date)+" "+ str(self.from_time) )
		to_datetime = get_datetime( str(self.to_date)+" "+ str(self.to_time) )
		self.total_hrs = flt(((to_datetime - from_datetime).total_seconds() / 60.0 / 60.0),2)