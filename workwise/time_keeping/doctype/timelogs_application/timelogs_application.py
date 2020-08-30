# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate, cstr, getdate
from frappe.model.document import Document
from workwise.time_keeping.application_utils import ( grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, get_employee_details,
change_owner, get_levelled_approval, get_levelled_approval_rejection, clear_approval_history, validate_inactive_employee, get_approver_email_list, get_cancelled_by_and_date, validate_approver_userperm, validate_cutoff_approval_date)

class TimelogsApplication(Document):
	def validate(self):
		get_employee_details(self)
		validate_inactive_employee(self)
		clear_approval_history(self)
		grant_head_subordinate_access(self)
		self.validate_fields()
		self.get_current_timecard()
		self.remove_duplicate_entry()
		change_owner(self)

	def on_submit(self):
		validate_approve_own_application(self)
		get_approver_and_date(self)
		get_approver_email_list(self, 'on_submit')
		validate_cutoff_approval_date(self)

	def before_update_after_submit(self):
		get_approver_email_list(self, 'before_update_after_submit')
		get_levelled_approval(self)
		validate_cutoff_approval_date(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		get_cancelled_by_and_date(self)

	def validate_fields(self):
		bio_id = frappe.get_value('Employee', self.employee, 'biometrics_id')
		if not bio_id:
			frappe.throw(_("<b>Timelogs Application: {0}</b><hr> Employee {1} has no Biometrics ID").format(self.name, self.employee_name))
		location = frappe.db.sql("""SELECT `name` FROM `tabLocation` WHERE `company` = %s """, (self.company), as_dict=True)
		cost_center = frappe.db.sql("""SELECT `name` FROM `tabCost Center` WHERE `company` = %s """, (self.company), as_dict=True)
		if self.location not in location:
			frappe.throw(_("Invalid Location: "+self.location))
		if self.cost_center not in cost_center:
			frappe.throw(_("Invalid Cost Center: "+self.cost_center))
		for t in self.timelogs:
			if t.location not in location:
				frappe.throw(_("Invalid Location: "+t.location))
			if t.location not in location:
				frappe.throw(_("Invalid Cost Center: "+t.cost_center))

	def get_current_timecard(self):
		#location = frappe.get_value('Employee', self.employee, 'location')
		#cost_center = frappe.get_value('Employee', self.employee, 'cost_center')
		for req in self.timelogs:
			if req.type == "Time In":
				card_type = 0
			if req.type == "Time Out":
				card_type = 1
			if req.type == "Break In":
				card_type = 2
			if req.type == "Break Out":
				card_type = 3

			current = frappe.db.sql("""SELECT TC.`name`, TC.`time` FROM `tabTime Card` TC INNER JOIN `tabEmployee` TE ON TC.biometrics_id = TE.biometrics_id
				WHERE TC.`date` = %s AND TC.`card_type` = %s AND TE.`name` = %s LIMIT 1 """, (getdate(req.target_date), card_type, self.employee), as_dict=True)
			if current:
				req.current = current[0].time
			else:
				req.current = None

			if not req.location:
				req.location = self.location
			if not req.cost_center:
				req.cost_center = self.cost_center

	def remove_duplicate_entry(self):
		unique_ent = []
		unique_entries = []
		for req in self.timelogs:
			if str(req.target_date)+str(req.type) not in unique_ent:
				unique_ent.append(str(req.target_date)+str(req.type));

				i = {
					"target_date": req.target_date,
					"type": req.type,
					"current": req.current,
					"request": req.request,
					"location": req.location,
					"cost_center": req.cost_center,
				}	
				unique_entries.append(i);

		self.set('timelogs', [])
		for ue in unique_entries:
			row = self.append('timelogs', {})
			row.update(ue)