# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import datetime, timedelta
from frappe import _
from frappe.utils import nowdate, get_time, flt, getdate
from frappe.model.document import Document
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs
from workwise.time_keeping.application_utils import grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, change_owner, get_levelled_approval, get_levelled_approval_rejection

class CompensatoryTimeOff(Document):
	def validate(self):
		grant_head_subordinate_access(self)
		if self.type == "File":
			self.validate_fields_file_cto()
			self.validate_duplicate_file_cto()
			self.validate_file_cto()
			self.get_timekeeping_settings()
		if self.type == "Use":
			self.validate_fields_use_cto()
			self.validate_use_cto()
			self.validate_date_use_cto()
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

	def get_timekeeping_settings(self):
		total_hrs = flt(self.total_hours, 2)
		cto_min_hrs = frappe.db.get_single_value('Timekeeping Settings', 'cto_min_hrs')
		if cto_min_hrs != 0:
			if total_hrs < flt(cto_min_hrs, 2):
				frappe.throw(_("Minimum hours of filing is {0}").format( cto_min_hrs ))
				
		cto_max_hrs = frappe.db.get_single_value('Timekeeping Settings', 'cto_max_hrs')
		if cto_max_hrs != 0:
			if total_hrs > flt(cto_max_hrs, 2):
				frappe.throw(_("Maximum hours of filing is {0}").format( cto_max_hrs ))

	#File CTO
	def validate_file_cto(self):
		from_date = datetime.strptime(str(self.date) + ' ' + str(self.from_time), '%Y-%m-%d %H:%M:%S')
		to_date = datetime.strptime(str(self.date) + ' ' + str(self.to_time), '%Y-%m-%d %H:%M:%S')
		if from_date <= to_date:
			total_hrs = to_date - from_date
		else:
			total_hrs = to_date - from_date + timedelta(days=1)
		self.total_hours = abs(flt(total_hrs.total_seconds() /60 /60, 2))
		self.credits_earned = flt(self.total_hours,2)/8
		if self.credits_earned > 1:
			self.credits_earned = 1.0

		self.balance = flt(self.credits_earned,2) - flt(self.credits_used,2)

	def validate_fields_file_cto(self):
		if not self.date:
			frappe.throw(_("Date is required"))

	def validate_duplicate_file_cto(self):
		existing_application = frappe.db.sql("""SELECT DISTINCT `name` FROM `tabCompensatory Time Off` WHERE `employee` = %s AND `type` = "File" AND `date` = %s AND `docstatus` = 1 LIMIT 1""",( self.employee, self.date ), as_dict=1)

		if existing_application:
			frappe.throw(_("Application already exists"))

	#Use CTO
	def validate_fields_use_cto(self):
		if not self.use_date:
			frappe.throw(_("Date is required"))

		cto_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_type == "Day":
			if not self.filed_cto:
				frappe.throw(_("Filed CTO is required"))

	def validate_use_cto(self):
		from_date = datetime.strptime(str(self.use_date) + ' ' + str(self.use_fromtime), '%Y-%m-%d %H:%M:%S')
		to_date = datetime.strptime(str(self.use_date) + ' ' + str(self.use_totime), '%Y-%m-%d %H:%M:%S')
		if from_date <= to_date:
			total_hrs = to_date - from_date
		else:
			total_hrs = to_date - from_date + timedelta(days=1)
		total_hours = abs(flt(total_hrs.total_seconds() /60 /60, 2))
		self.use_total_hours = total_hours
		self.required_credits = flt(total_hours,2)/8
		if self.required_credits > 1:
			self.required_credits = 1.0

		total_credits_earned = 0.00
		date_list = []
		last_date = ""
		
		cto_use_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_use_type == "Day":
			current_credits = frappe.db.sql("""SELECT credits_earned - credits_used as cred_balance, `date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %s AND `docstatus` = 1 AND `name` = %s ORDER BY `date` DESC""",( self.employee, self.filed_cto ), as_dict=1)
		else:
			current_credits = frappe.db.sql("""SELECT credits_earned - credits_used as cred_balance, `date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %s AND `docstatus` = 1 ORDER BY `date` DESC""",( self.employee ), as_dict=1)

		if current_credits:
			for d in current_credits:
				total_credits_earned += flt(d.cred_balance, 2)
				date_list.append(d.date)

			last_date = date_list[-1]

		self.total_credits_earned = total_credits_earned

		if flt(self.required_credits, 2) > flt(self.total_credits_earned, 2):
			frappe.throw(_("You dont have enough credits"))
		
		return last_date

	def validate_date_use_cto(self):
		last_date = self.validate_use_cto()
		if getdate(self.use_date) < getdate(last_date):
			frappe.throw(_("Cannot Use CTO Application for date {0} because last Filed CTO Application date is {1}").format(self.use_date, last_date))

	def deduct_use_cto(self):
		entries = [] 
		req_credits = flt(self.required_credits, 2)

		cto_use_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_use_type == "Day":
			filed_cto = frappe.db.sql("""SELECT `name`, `credits_earned`, credits_used, balance, `date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %s AND `docstatus` = 1 AND `name` = %s """,( self.employee, self.filed_cto ), as_dict=1)
		else:
			filed_cto = frappe.db.sql("""SELECT `name`, `credits_earned`, credits_used, balance, `date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %s AND `docstatus` = 1 AND `balance` > 0 ORDER BY `date` ASC""",( self.employee ), as_dict=1)

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
					
					frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET `balance` = %s, credits_used = %s WHERE `name` = %s AND docstatus = 1 """, (remain_bal, cred_used, a.name))
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
			frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET credits_used = credits_used - %s WHERE `name` = %s AND docstatus = 1 """, (a.credits_used, a.filed_cto))
			frappe.db.commit()

			frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET `balance` = (credits_earned - credits_used) WHERE `name` = %s AND docstatus = 1 """, (a.filed_cto))
			frappe.db.commit()

			frappe.db.sql(""" DELETE FROM `tabCompensatory Time Off Table` WHERE filed_cto = %s AND `date` = %s """, (a.filed_cto, a.date))
			frappe.db.commit()

	#Cancel File CTO
	def validate_cancel_file_cto(self):
		filed_cto = frappe.db.sql(""" SELECT `parent` FROM `tabCompensatory Time Off Table` WHERE `filed_cto` = %s """,( self.name ), as_dict=1)
		if filed_cto:
			for d in filed_cto:
				frappe.throw(_("Cannot cancel because CTO Application {0} is linked with CTO Application {1}").format(self.name, d.parent))