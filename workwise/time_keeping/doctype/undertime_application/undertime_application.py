# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import datetime
from frappe import _
from frappe.utils import nowdate, get_time, flt
from frappe.model.document import Document
from workwise.time_keeping.application_utils import ( grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, 
change_owner, get_levelled_approval, get_levelled_approval_rejection, clear_approval_history, validate_inactive_employee, get_approver_email_list, get_cancelled_by_and_date )

class UndertimeApplication(Document):
	def validate(self):
		validate_inactive_employee(self)
		clear_approval_history(self)
		grant_head_subordinate_access(self)
		total_hrs = datetime.strptime(str(self.to_time), '%H:%M:%S') - datetime.strptime(str(self.from_time), '%H:%M:%S')
		self.total_hrs = flt((total_hrs.total_seconds() / 60.0 / 60.0),2)
		change_owner(self)

	def on_submit(self):
		validate_approve_own_application(self)
		get_approver_and_date(self)
		get_approver_email_list(self, 'on_submit')

	def before_update_after_submit(self):
		get_approver_email_list(self, 'before_update_after_submit')
		get_levelled_approval(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		get_cancelled_by_and_date(self)