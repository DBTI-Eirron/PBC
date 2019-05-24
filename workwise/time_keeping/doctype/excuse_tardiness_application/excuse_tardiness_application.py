# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime
from frappe import _
from frappe.utils import nowdate
from frappe.model.document import Document
from workwise.time_keeping.attendance_utils import get_schedule
from workwise.time_keeping.application_utils import ( grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, 
change_owner, get_levelled_approval, get_levelled_approval_rejection, clear_approval_history, validate_inactive_employee)

class ExcuseTardinessApplication(Document):
	def validate(self):
		validate_inactive_employee(self)
		clear_approval_history(self)
		time_in, time_out = self.get_timelogs()
		if not time_in and not time_out:
			has_ob = self.check_employee_ob()
			if not has_ob:
				frappe.throw(_("<b>Excuse Tardiness Application: {0}</b><hr> No timelogs for employee {1}").format(self.name, self.employee))
		grant_head_subordinate_access(self)
		change_owner(self)

	def on_submit(self):
		validate_approve_own_application(self)
		get_approver_and_date(self)

	def before_update_after_submit(self):
		get_levelled_approval(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)

	def load_timecard(self):
		time_in, time_out = self.get_timelogs()
		if time_in:
			self.to_time = time_in
		if time_out:
			self.from_time = time_out

	def get_timelogs(self):
		time_in = None
		time_out = None

		bio_id = frappe.get_value("Employee", self.employee, "biometrics_id")
		if bio_id:
			time_out = frappe.db.sql(""" SELECT `time` FROM `tabTime Card` WHERE `biometrics_id` = %s AND `card_type` = 0 AND `is_disabled` = 0 AND `date` = %s LIMIT 1 """, (bio_id, self.date), as_dict=True)
			time_in = frappe.db.sql(""" SELECT `time` FROM `tabTime Card` WHERE `biometrics_id` = %s AND `card_type` = 1 AND `is_disabled` = 0 AND `date` = %s LIMIT 1 """, (bio_id, self.date), as_dict=True)
			if time_in:
				to_time = time_in[0].time
			if time_out:
				from_time = time_out[0].time

		schedule = get_schedule(self.employee, self.date, self.date)
		if schedule:
			work_sched = frappe.db.sql("""SELECT DISTINCT `o_time_in`, `o_time_out` FROM `tabWork Schedule` WHERE `work_shift` = %s AND `employee` = %s AND `target_date` = %s LIMIT 1""",(schedule[0].work_shift, self.employee, self.date), as_dict=True)
			for ws in work_sched:
				if ws.o_time_in:
					time_in = datetime.strftime(ws.o_time_in, '%H:%M:%S')
				if ws.o_time_out:
					time_out = datetime.strftime(ws.o_time_out, '%H:%M:%S')

		return time_in, time_out

	def check_employee_ob(self):
		ob_apps = frappe.db.sql("""SELECT OBA.`name`FROM `tabOfficial Business Application Table` OBAT INNER JOIN `tabOfficial Business Application` OBA  ON OBAT.parent = OBA.`name`
			WHERE OBA.employee = %s AND OBA.workflow_state = 'Approved' AND OBAT.target_date = %s AND OBAT.is_excluded = 0 """,(self.employee, self.date), as_dict=1)