# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime
from frappe import _
from frappe.utils import nowdate, get_datetime, cstr, getdate, get_time
from frappe.model.document import Document
from workwise.time_keeping.attendance_utils import get_schedule, get_actual_logs
from workwise.time_keeping.application_utils import ( grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, change_owner, get_levelled_approval, 
	get_levelled_approval_rejection, clear_approval_history, validate_inactive_employee, get_approver_email_list, get_cancelled_by_and_date, validate_approver_userperm, validate_cutoff_approval_date, get_employee_details )

class ExcuseTardinessApplication(Document):
	def validate(self):
		get_employee_details(self)
		validate_inactive_employee(self)
		clear_approval_history(self)
		time_in, time_out = self.get_employeee_actual_logs()
		if not time_in and not time_out:
			frappe.throw(_("<b>Excuse Tardiness Application: {0}</b><hr> No timelogs for employee {1}").format(self.name, self.employee))
		self.get_recipients()
		grant_head_subordinate_access(self)
		change_owner(self)

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

	def load_timecard(self):
		time_in, time_out = self.get_employeee_actual_logs()
		if time_in:
			self.to_time = datetime.strftime(time_in, "%H:%M:%S")
		if time_out:
			self.from_time = datetime.strftime(time_out, "%H:%M:%S")

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
			work_sched = frappe.db.sql("""SELECT DISTINCT `o_time_in`, `o_time_out` FROM `tabWork Schedule` WHERE `work_shift` = %s AND `employee` = %s AND `target_date` = %s LIMIT 1""",(schedule[0]['work_shift'], self.employee, self.date), as_dict=True)
			for ws in work_sched:
				if ws.o_time_in:
					time_in = datetime.strftime(ws.o_time_in, '%H:%M:%S')
				if ws.o_time_out:
					time_out = datetime.strftime(ws.o_time_out, '%H:%M:%S')

		return time_in, time_out

	def get_employeee_actual_logs(self):
		#get_timelogs_reference
		actual_in = None
		actual_out = None

		override = frappe.db.sql(""" SELECT time_in, time_out FROM `tabOverride List`
			WHERE target_date = %s and employee = %s  """,(self.date, self.employee), as_dict=True)

		ob_apps = frappe.db.sql("""SELECT OBAT.target_date, OBAT.date, OBAT.to_date,OBAT.from_time, OBAT.to_time 
			FROM `tabOfficial Business Application Table` OBAT
			INNER JOIN `tabOfficial Business Application` OBA  ON OBAT.parent = OBA.`name` INNER JOIN `tabPayroll Period` PP ON OBA.`company` = PP.`company`
			WHERE OBA.workflow_state = 'Approved' AND OBAT.target_date = %s AND OBAT.is_excluded = 0 AND OBA.approved_on <= PP.approval_cutoff  and OBA.employee = %s
			AND OBAT.`target_date` BETWEEN PP.`attendance_from` and PP.`attendance_to` """, (self.date, self.employee), as_dict=1)
		
		actual_logs = get_actual_logs(self.employee, getdate(self.date), getdate(self.date), 1)

		dtrp_apps = frappe.db.sql("""SELECT DA.`name`,DT.`type`, DA.`employee`, TIMESTAMP(DA.`target_date`, DT.`request`) as card_datetime, 
			DA.`target_date`, DT.`request`, DT.`type`, DA.`approved_on`, DT.`card_type`
			FROM `tabDTR Problem Table` DT INNER JOIN `tabDTR Problem Application` DA ON DT.`parent`=DA.`name` 
			WHERE DA.`workflow_state` = 'Approved' AND DA.`employee` = %s
			AND DA.`target_date` = %s
			ORDER BY card_datetime """, (self.employee, self.date), as_dict=1)
		
		if actual_logs:
			if actual_logs[0]["card_in"]:
				actual_in = actual_logs[0]["card_in"]
			else:
				actual_in = None
			if actual_logs[0]["card_out"]:
				actual_out = actual_logs[0]["card_out"]
			else:
				actual_out = None

		if override:
			for o in override:
				if o.time_in:
					actual_in = o.time_in

				if o.time_out:
					actual_out = o.time_out
	
		if ob_apps:
			for ob in ob_apps:
				ob_in = get_datetime( str(ob.date)+" "+ str(ob.from_time))
				ob_out = get_datetime( str(ob.to_date)+" "+ str(ob.to_time))
				if actual_in:
					if get_datetime(ob_in)< get_datetime(actual_in):
						actual_in = ob_in
				else:
					actual_in = ob_in
				if actual_out:
					if get_datetime(ob_out)> get_datetime(actual_out):
						actual_out = ob_out
				else:
					actual_out = ob_out

		return actual_in, actual_out

	def get_recipients(self):
		recipients = []
		managers = frappe.db.sql("""SELECT ES.employee, E.user_id FROM `tabEmployee Subordinates` ES 
			INNER JOIN `tabSubordinates` S ON S.parent = ES.name
			LEFT JOIN `tabEmployee` E ON ES.employee = E.name
			WHERE S.subordinate = %s """,(self.employee), as_dict=True)
		for d in managers:
			if d.user_id:
				recipients.append(d.user_id)

		if recipients:
			send_to = ', '.join(str(x) for x in recipients)
			self.managers_list = send_to