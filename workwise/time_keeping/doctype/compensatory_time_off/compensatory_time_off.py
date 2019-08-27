# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import datetime, timedelta
from frappe import _
from frappe.utils import nowdate, get_time, flt, getdate
from frappe.model.document import Document
from workwise.time_keeping.attendance_utils import get_schedule, get_ob_list
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs
from workwise.time_keeping.application_utils import ( grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, 
change_owner, get_levelled_approval, get_levelled_approval_rejection, clear_approval_history, validate_inactive_employee, get_approver_email_list, get_cancelled_by_and_date, get_current_logs )

class CompensatoryTimeOff(Document):
	def validate(self):
		validate_inactive_employee(self)
		clear_approval_history(self)
		grant_head_subordinate_access(self)
		if self.type == "File":
			self.validate_fields_file_cto()
			self.validate_duplicate_file_cto()
			self.validate_file_cto()
			self.get_cto_workshift_file_setup()
			self.validate_credits_earned()
		if self.type == "Use":
			self.validate_fields_use_cto()
			self.validate_use_cto()
			self.validate_date_use_cto()
			self.validate_use_credits()
			self.get_cto_workshift_use_setup()
			self.validate_required_credits()
		change_owner(self)

	def on_submit(self):
		validate_approve_own_application(self)
		if self.type == "Use":
			emp_app = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
			if emp_app < 1:
				self.deduct_use_cto()
		get_approver_and_date(self)
		get_approver_email_list(self, 'on_submit')

	def before_update_after_submit(self):
		if self.type == "Use":
			emp_app = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
			if emp_app > 0:
				self.deduct_use_cto()

		get_approver_email_list(self, 'before_update_after_submit')
		get_levelled_approval(self)

	#def on_update_after_submit(self):
	#	if self.type == "Use":
	#		emp_app = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
	#		if emp_app > 0:
	#			if self.workflow_state == "Approved":
	#				self.deduct_use_cto()

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		if self.type == "File":
			self.validate_cancel_file_cto()
		if self.type == "Use":
			self.revert_credit_deductions()
		get_cancelled_by_and_date(self)

	def get_timekeeping_settings_for_cto_use_type(self):
		cto_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_type == "Day":
			return 'day'
		else:
			return 'hour'

	def get_cto_workshift_file_setup(self):
		schedule = get_schedule(self.employee, self.date, self.date)
		if schedule:
			shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0]['work_shift']), as_dict=True)
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
			shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0]['work_shift']), as_dict=True)
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

		cto_filed_credits_on_logs = frappe.db.get_single_value('Timekeeping Settings', 'cto_filed_credits_on_logs')
		if cto_filed_credits_on_logs:
			from_date, to_date = self.validate_cto_filed_credits_on_logs(from_date, to_date)

		if from_date <= to_date:
			total_hrs = to_date - from_date
		else:
			total_hrs = to_date - from_date + timedelta(days=1)
		self.get_autobreak_hrs()	
		total_hours = abs(flt(total_hrs.total_seconds() /60 /60, 2))
		total_hours = flt(total_hours, 2) - flt(self.break_hours, 2)
		self.total_hours = flt(total_hours, 2)

		work_hours = 8
		schedule = get_schedule(self.employee, self.date, self.date)
		if schedule:
			for d in schedule:
				if d['work_hours'] > 0:
					work_hours = flt(d['work_hours'])
				else:
					work_hours = 8

		if work_hours > 0:
			file_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_file_type')
			if file_type == "Day":
				self.credits_earned = flt(self.total_hours,2)/flt(work_hours, 2)
				if self.credits_earned > 1:
					self.credits_earned = 1.0
			else:
				self.credits_earned = flt(self.total_hours,2)/flt(work_hours, 2)

		self.balance = self.credits_earned - self.credits_used

	def validate_cto_filed_credits_on_logs(self, from_date, to_date):
		tc_from_date, tc_to_date, ob_from_date, ob_to_date = None, None, None, None

		time_in, time_out = get_current_logs(self.employee, getdate(self.date))
		if (time_in) or (time_out):
			tc_from_date = datetime.strptime(str(time_in), '%Y-%m-%d %H:%M:%S')
			tc_to_date = datetime.strptime(str(time_out), '%Y-%m-%d %H:%M:%S')

		obs = get_ob_list(self.employee, getdate(self.date), getdate(self.date), getdate(self.date), 0)
		for ob in obs:
			if ob_from_date:
				if datetime.strptime(str(ob.target_date) + ' ' + str(ob.from_time), '%Y-%m-%d %H:%M:%S') < ob_from_date:
					ob_from_date = datetime.strptime(str(ob.target_date) + ' ' + str(ob.from_time), '%Y-%m-%d %H:%M:%S')
			else:
				ob_from_date = datetime.strptime(str(ob.target_date) + ' ' + str(ob.from_time), '%Y-%m-%d %H:%M:%S')

			if ob_to_date:
				if datetime.strptime(str(ob.target_date) + ' ' + str(ob.to_time), '%Y-%m-%d %H:%M:%S') > ob_to_date:
					ob_to_date = datetime.strptime(str(ob.target_date) + ' ' + str(ob.to_time), '%Y-%m-%d %H:%M:%S')
			else:
				ob_to_date = datetime.strptime(str(ob.target_date) + ' ' + str(ob.to_time), '%Y-%m-%d %H:%M:%S')

		if tc_from_date:
			from_date = tc_from_date
		if ob_from_date:
			from_date = ob_from_date
		if tc_to_date:
			to_date = tc_to_date
		if ob_to_date:
			to_date = ob_to_date
		if (tc_from_date) and (ob_from_date):
			if tc_from_date < ob_from_date:
				from_date = tc_from_date
			else:
				from_date = ob_from_date
		if (tc_to_date) and (ob_to_date):
			if tc_to_date > ob_to_date:
				to_date = tc_to_date
			else:
				to_date = ob_to_date

		return from_date, to_date

	def validate_fields_file_cto(self):
		if not self.date:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Date is required").format(self.name))

	def validate_credits_earned(self):
		if self.credits_earned <= 0:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Credits Earned must be greater than 0").format(self.name))

	def validate_required_credits(self):
		if self.required_credits <= 0:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Required Credits must be greater than 0").format(self.name))

	def validate_duplicate_file_cto(self):
		existing_application = frappe.db.sql("""SELECT DISTINCT `name`, `date`, from_time, to_time FROM `tabCompensatory Time Off` WHERE `employee` = %s AND `type` = "File" AND `date` = %s AND `docstatus` = 1 AND `workflow_state` = "Approved" LIMIT 1""",( self.employee, self.date ), as_dict=1)
		if existing_application:
			for d in existing_application:
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

	def get_autobreak_hrs(self):
		if self.is_new():
			if not self.amended_from:
				if not self.break_hours:
					self.break_hours = 0.00

		if self.type == "Use":
			schedule = get_schedule(self.employee, self.use_date, self.use_date)
		else:
			schedule = get_schedule(self.employee, self.date, self.date)
			
		if schedule:
			shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0]['work_shift']), as_dict=True)
			if shifts:
				autobreak_setup = frappe.db.sql("""SELECT break_mins, from_hrs, to_hrs FROM `tabCTO Auto Break Table` WHERE `parenttype` = "Work Shift" AND `parent` = %s """,(shifts[0].name), as_dict=True)
				if autobreak_setup:
					self.break_hours = 0.00
					self.use_break_hours = 0.00
					for a in autobreak_setup:
						if self.type == "Use":
							if a.from_hrs <= self.use_total_hours <= a.to_hrs:
								self.use_break_hours = flt(a.break_mins, 2)/60
								break
						else:
							if a.from_hrs <= self.total_hours <= a.to_hrs:
								self.break_hours = flt(a.break_mins, 2)/60
								break

	def validate_use_cto(self):
		from_date = datetime.strptime(str(self.use_date) + ' ' + str(self.use_fromtime), '%Y-%m-%d %H:%M:%S')
		to_date = datetime.strptime(str(self.use_date) + ' ' + str(self.use_totime), '%Y-%m-%d %H:%M:%S')
		if from_date <= to_date:
			total_hrs = to_date - from_date
		else:
			total_hrs = to_date - from_date + timedelta(days=1)
		self.get_autobreak_hrs()	
		total_hours = abs(flt(total_hrs.total_seconds() /60 /60, 2))
		total_hours = flt(total_hours, 2) - flt(self.use_break_hours, 2)
		self.use_total_hours = total_hours

		work_hours = 8
		schedule = get_schedule(self.employee, self.use_date, self.use_date)
		if schedule:
			for d in schedule:
				if d['work_hours'] > 0:
					work_hours = flt(d['work_hours'])
				else:
					work_hours = 8

		if work_hours > 0:
			self.required_credits = flt(total_hours,2)/flt(work_hours, 2)
			#if self.required_credits > 1:
			#	self.required_credits = 1.0

		total_credits_earned = 0.00
		date_list = []
		last_date = ""
		
		cto_validity = frappe.db.get_single_value('Timekeeping Settings', 'cto_validity')
		cto_use_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_validity > 0:
			cto_validity_condition = " AND (%(use_date)s BETWEEN `date` AND DATE_SUB(`date`, INTERVAL -"+int(cto_validity)+" DAY)) "
		else:
			cto_validity_condition = ""

		if cto_use_type == "Day":
			current_credits = frappe.db.sql("""SELECT credits_earned - credits_used as cred_balance, `date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %(employee)s AND `docstatus` = 1 AND `workflow_state` = "Approved" AND `name` = %(filed_cto)s AND `balance` > 0 {conditions} """.format(conditions=cto_validity_condition),{
				"employee": self.employee,
				"filed_cto": self.filed_cto,
				"use_date": getdate(self.use_date),
				"cto_validity": cto_validity,
			}, as_dict=True)
		else:
			current_credits = frappe.db.sql("""SELECT credits_earned - credits_used as cred_balance, `date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %(employee)s AND `docstatus` = 1 AND `workflow_state` = 'Approved' AND `balance` > 0 {conditions} ORDER BY `date` ASC """.format(conditions=cto_validity_condition),{
				"employee": self.employee,
				"use_date": getdate(self.use_date),
				"cto_validity": cto_validity,
			}, as_dict=True)

		if current_credits:
			for d in current_credits:
				total_credits_earned += d.cred_balance
				date_list.append(d.date)

			last_date = date_list[-1]

		self.total_credits_earned = total_credits_earned
		
		return last_date

	def validate_use_credits(self):
		if self.required_credits > self.total_credits_earned:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> You dont have enough credits").format(self.name))

	def validate_date_use_cto(self):
		last_date = self.validate_use_cto()
		if last_date:
			if getdate(self.use_date) < getdate(last_date):
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Cannot Use CTO Application for date {1} because last Filed CTO Application date is {2}").format(self.name, self.use_date, last_date))

	def deduct_use_cto(self):
		entries = [] 
		req_credits = self.required_credits

		cto_validity = frappe.db.get_single_value('Timekeeping Settings', 'cto_validity')
		cto_use_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_validity > 0:
			cto_validity_condition = " AND (%(use_date)s BETWEEN `date` AND DATE_SUB(`date`, INTERVAL -"+int(cto_validity)+" DAY)) "
		else:
			cto_validity_condition = ""

		if cto_use_type == "Day":
			filed_cto = frappe.db.sql("""SELECT `name`, `credits_earned`, credits_used, balance, `date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %(employee)s AND `docstatus` = 1 AND `workflow_state` = "Approved" AND `name` = %(filed_cto)s AND `balance` > 0 {conditions} """.format(conditions=cto_validity_condition),{
				"employee": self.employee,
				"filed_cto": self.filed_cto,
				"use_date": getdate(self.use_date),
				"cto_validity": cto_validity,
				}, as_dict=True)
		else:
			filed_cto = frappe.db.sql("""SELECT `name`, `credits_earned`, credits_used, balance, `date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %(employee)s AND `docstatus` = 1 AND `workflow_state` = "Approved" AND `balance` > 0 {conditions} ORDER BY `date` ASC""".format(conditions=cto_validity_condition),{
				"employee": self.employee,
				"use_date": getdate(self.use_date),
				"cto_validity": cto_validity,
				}, as_dict=True)

		if filed_cto:
			#Validate credits
			fc_credits_earned = 0.00
			for fc in filed_cto:
				fc_credits_earned += fc.balance
			if fc_credits_earned < req_credits:
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> You dont have enough credits").format(self.name))
			#Map CTO
			for a in filed_cto:
				if req_credits > 0: 
					cred_used = 0.0
					if a.balance > 0:
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
							"credits_used": cred_used - flt(a.balance, 2) if cred_used > a.balance else cred_used
						}
						entries.append(row);
						
						frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET `balance` = %s, credits_used = %s WHERE `name` = %s AND docstatus = 1 AND `workflow_state` = "Approved" """, (remain_bal, cred_used, a.name))
						frappe.db.commit()
				else:
					break

			for d in entries:
				row = self.append('use_cto_table', {})
				row.update(d)
				#row.save(d)
		else:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> You dont have enough credits").format(self.name))

	#Cancel Use CTO
	def revert_credit_deductions(self):
		for a in self.get('use_cto_table'):
			frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET credits_used = credits_used - %s WHERE `name` = %s AND docstatus = 1 AND `workflow_state` = "Approved" """, (a.credits_used, a.filed_cto))
			frappe.db.commit()

			frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET `balance` = (credits_earned - credits_used) WHERE `name` = %s AND docstatus = 1 AND `workflow_state` = "Approved" """, (a.filed_cto))
			frappe.db.commit()

			frappe.db.sql(""" DELETE FROM `tabCompensatory Time Off Table` WHERE filed_cto = %s AND `date` = %s AND docstatus = 1 """, (a.filed_cto, a.date))
			frappe.db.commit()

	#Cancel File CTO
	def validate_cancel_file_cto(self):
		filed_cto = frappe.db.sql(""" SELECT `parent` FROM `tabCompensatory Time Off Table` WHERE `filed_cto` = %s """,( self.name ), as_dict=1)
		if filed_cto:
			for d in filed_cto:
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Cannot cancel because CTO Application {1} is linked with CTO Application {2}").format(self.name, self.name, d.parent))