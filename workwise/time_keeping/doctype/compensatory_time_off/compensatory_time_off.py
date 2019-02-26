# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import datetime, timedelta
from frappe import _
from frappe.utils import nowdate, get_time, flt, getdate
from frappe.model.document import Document
from workwise.time_keeping.attendance_utils import get_schedule
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs
from workwise.time_keeping.application_utils import grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, change_owner, get_levelled_approval, get_levelled_approval_rejection

class CompensatoryTimeOff(Document):
	def validate(self):
		grant_head_subordinate_access(self)
		if self.type == "File":
			self.validate_fields_file_cto()
			self.validate_duplicate_file_cto()
			self.validate_file_cto()
			self.get_cto_workshift_file_setup()
		if self.type == "Use":
			self.validate_fields_use_cto()
			self.validate_use_cto()
			self.validate_date_use_cto()
			self.get_cto_workshift_use_setup()
		change_owner(self)

	def on_submit(self):
		validate_approve_own_application(self)
		if self.type == "Use":
			self.deduct_use_cto()
		get_approver_and_date(self)

	def before_update_after_submit(self):
		get_levelled_approval(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		if self.type == "File":
			self.validate_cancel_file_cto()
		if self.type == "Use":
			self.revert_credit_deductions()

	def get_timekeeping_settings_for_cto_use_type(self):
		cto_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_type == "Day":
			return 'day'
		else:
			return 'hour'

	def get_cto_workshift_file_setup(self):
		schedule = get_schedule(self.employee, self.date, self.date)
		if schedule:
			shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0].work_shift), as_dict=True)
			if shifts:
				if self.type == "File":
					if shifts[0].cto_min_filing_hrs > 0:
						if self.total_hours < shifts[0].cto_min_filing_hrs:
							frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Minimum hours of filing is {1}").format(self.name, shifts[0].cto_min_filing_hrs))
					if shifts[0].cto_max_filing_hrs > 0:
						if self.total_hours > shifts[0].cto_max_filing_hrs:
							frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Maximum hours of filing is {1}").format(self.name, shifts[0].cto_max_filing_hrs))

	def get_cto_workshift_use_setup(self):
		schedule = get_schedule(self.employee, self.use_date, self.use_date)
		if schedule:
			shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0].work_shift), as_dict=True)
			if shifts:
				if self.type == "Use":
					if shifts[0].cto_min_usage_hrs > 0:
						if self.use_total_hours < shifts[0].cto_min_usage_hrs:
							frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Minimum hours of usage is {1}").format(self.name, shifts[0].cto_min_usage_hrs))
					if shifts[0].cto_max_usage_hrs > 0:
						if self.use_total_hours > shifts[0].cto_max_usage_hrs:
							frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Maximum hours of usage is {1}").format(self.name, shifts[0].cto_max_usage_hrs))

	#File CTO
	def validate_file_cto(self):
		from_date = datetime.strptime(str(self.date) + ' ' + str(self.from_time), '%Y-%m-%d %H:%M:%S')
		to_date = datetime.strptime(str(self.date) + ' ' + str(self.to_time), '%Y-%m-%d %H:%M:%S')
		if from_date <= to_date:
			total_hrs = to_date - from_date
		else:
			total_hrs = to_date - from_date + timedelta(days=1)
		self.total_hours = abs(flt(total_hrs.total_seconds() /60 /60, 2))

		work_hours = 8
		schedule = get_schedule(self.employee, self.date, self.date)
		if schedule:
			for d in schedule:
				work_hours = d.work_hours

		self.credits_earned = flt(self.total_hours,2)/flt(work_hours, 2)
		if self.credits_earned > 1:
			self.credits_earned = 1.0

		self.balance = flt(self.credits_earned,2) - flt(self.credits_used,2)

	def validate_fields_file_cto(self):
		if not self.date:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Date is required").format(self.name))

	def validate_duplicate_file_cto(self):
		existing_application = frappe.db.sql("""SELECT DISTINCT `name`, `date`, from_time, to_time FROM `tabCompensatory Time Off` WHERE `employee` = %s AND `type` = "File" AND `date` = %s AND `docstatus` = 1 AND `workflow_state` = "Approved" LIMIT 1""",( self.employee, self.date ), as_dict=1)
		if existing_application:
			for d in existing_application:
				#frappe.throw(_(d.date))
				existing_from = datetime.strptime(str(d.date) + ' ' + str(d.from_time), '%Y-%m-%d %H:%M:%S')
				existing_to = datetime.strptime(str(d.date) + ' ' + str(d.to_time), '%Y-%m-%d %H:%M:%S')
				
				cur_from = datetime.strptime(str(self.date) + ' ' + str(self.from_time), '%Y-%m-%d %H:%M:%S')
				cur_to = datetime.strptime(str(self.date) + ' ' + str(self.to_time), '%Y-%m-%d %H:%M:%S')

				if existing_from <= cur_from <= existing_to or existing_from <= cur_to <= existing_to:
					frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Compensatory Time Off Application already exists, {1}").format(self.name, d.name))

	#Use CTO
	def validate_fields_use_cto(self):
		if not self.use_date:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Date is required").format(self.name))

		cto_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_type == "Day":
			if not self.filed_cto:
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Filed CTO is required").format(self.name))

	def validate_use_cto(self):
		from_date = datetime.strptime(str(self.use_date) + ' ' + str(self.use_fromtime), '%Y-%m-%d %H:%M:%S')
		to_date = datetime.strptime(str(self.use_date) + ' ' + str(self.use_totime), '%Y-%m-%d %H:%M:%S')
		if from_date <= to_date:
			total_hrs = to_date - from_date
		else:
			total_hrs = to_date - from_date + timedelta(days=1)
		total_hours = abs(flt(total_hrs.total_seconds() /60 /60, 2))
		self.use_total_hours = total_hours

		work_hours = 8
		schedule = get_schedule(self.employee, self.use_date, self.use_date)
		if schedule:
			for d in schedule:
				work_hours = d.work_hours

		self.required_credits = flt(total_hours,2)/flt(work_hours, 2)
		if self.required_credits > 1:
			self.required_credits = 1.0

		total_credits_earned = 0.00
		date_list = []
		last_date = ""
		
		cto_use_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_use_type == "Day":
			current_credits = frappe.db.sql("""SELECT credits_earned - credits_used as cred_balance, `date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %s AND `docstatus` = 1 AND `workflow_state` = "Approved" AND `name` = %s ORDER BY `date` DESC""",( self.employee, self.filed_cto ), as_dict=1)
		else:
			current_credits = frappe.db.sql("""SELECT credits_earned - credits_used as cred_balance, `date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %s AND `docstatus` = 1 AND `workflow_state` = "Approved" ORDER BY `date` DESC""",( self.employee ), as_dict=1)

		if current_credits:
			for d in current_credits:
				total_credits_earned += flt(d.cred_balance, 2)
				date_list.append(d.date)

			last_date = date_list[-1]

		self.total_credits_earned = total_credits_earned

		if flt(self.required_credits, 2) > flt(self.total_credits_earned, 2):
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> You dont have enough credits").format(self.name))
		
		return last_date

	def validate_date_use_cto(self):
		last_date = self.validate_use_cto()
		if getdate(self.use_date) < getdate(last_date):
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Cannot Use CTO Application for date {1} because last Filed CTO Application date is {2}").format(self.name, self.use_date, last_date))

	def deduct_use_cto(self):
		entries = [] 
		req_credits = flt(self.required_credits, 2)

		cto_use_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_use_type == "Day":
			filed_cto = frappe.db.sql("""SELECT `name`, `credits_earned`, credits_used, balance, `date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %s AND `docstatus` = 1 AND `workflow_state` = "Approved" AND `name` = %s """,( self.employee, self.filed_cto ), as_dict=1)
		else:
			filed_cto = frappe.db.sql("""SELECT `name`, `credits_earned`, credits_used, balance, `date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %s AND `docstatus` = 1 AND `workflow_state` = "Approved" AND `balance` > 0 ORDER BY `date` ASC""",( self.employee ), as_dict=1)

		if filed_cto:
			for a in filed_cto:
				cred_used = 0.0
				if req_credits > 0: 
					if a.balance >= req_credits:
						remain_bal = a.balance - req_credits
						cred_used = a.credits_used + req_credits
						req_credits = 0.0
					else:
						remain_bal = 0.0
						req_credits = req_credits - a.balance
						cred_used = a.balance
					
					row = {
						"filed_cto": a.name,
						"date": a.date,
						"balance": a.balance,
						"credits_used": cred_used
					}
					entries.append(row);
					
					frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET `balance` = %s, credits_used = %s WHERE `name` = %s AND docstatus = 1 AND `workflow_state` = "Approved" """, (remain_bal, cred_used, a.name))
					frappe.db.commit()
				else:
					break

			for d in entries:
				row = self.append('use_cto_table', {})
				row.update(d)
				row.save(d)

	#Cancel Use CTO
	def revert_credit_deductions(self):
		for a in self.get('use_cto_table'):
			frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET credits_used = credits_used - %s WHERE `name` = %s AND docstatus = 1 AND `workflow_state` = "Approved" """, (a.credits_used, a.filed_cto))
			frappe.db.commit()

			frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET `balance` = (credits_earned - credits_used) WHERE `name` = %s AND docstatus = 1 AND `workflow_state` = "Approved" """, (a.filed_cto))
			frappe.db.commit()

			frappe.db.sql(""" DELETE FROM `tabCompensatory Time Off Table` WHERE filed_cto = %s AND `date` = %s """, (a.filed_cto, a.date))
			frappe.db.commit()

	#Cancel File CTO
	def validate_cancel_file_cto(self):
		filed_cto = frappe.db.sql(""" SELECT `parent` FROM `tabCompensatory Time Off Table` WHERE `filed_cto` = %s """,( self.name ), as_dict=1)
		if filed_cto:
			for d in filed_cto:
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Cannot cancel because CTO Application {1} is linked with CTO Application {2}").format(self.name, self.name, d.parent))