# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, calendar
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
		self.clear_fields()
		self.file_validate_cto()
		self.use_validate_cto()

	def before_submit(self):
		validate_approve_own_application(self)
		if not frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers'):
			self.use_deduct_cto()

	def on_submit(self):
		get_approver_and_date(self)
		get_approver_email_list(self, 'on_submit')

	def before_update_after_submit(self):
		if frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers'):
			self.use_validate_deduct()
		get_approver_email_list(self, 'before_update_after_submit')
		get_levelled_approval(self)

	def on_update_after_submit(self):
		if self.workflow_state == "Approved":
			if frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers'):
				self.use_deduct_cto()

	def on_cancel(self):
		self.file_cancel_cto()
		self.revert_credit_deductions()
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		get_cancelled_by_and_date(self)

	#GENERAL
	def get_timekeeping_settings_for_cto_use_type(self):
		cto_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_type == "Day":
			return 'day'
		else:
			return 'hour'

	def get_target_date(self):
		if self.type == "File":
			self.file_get_target_date()

		if self.type == "Use":
			self.use_get_target_date()

	def clear_fields(self):
		if self.is_new():
			self.use_cto_table = None

	def get_autobreak_hrs(self, total_hours):
		if self.is_new():
			if not self.amended_from:
				if not self.break_hours:
					self.break_hours = 0.00

		if self.type == "Use":
			schedule = get_schedule(self.employee, self.use_target_date, self.use_target_date)
		else:
			schedule = get_schedule(self.employee, self.file_target_date, self.file_target_date)
			
		if schedule:
			shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0]['work_shift']), as_dict=True)
			if shifts:
				autobreak_setup = frappe.db.sql("""SELECT break_mins, from_hrs, to_hrs FROM `tabCTO Auto Break Table` WHERE `parenttype` = "Work Shift" AND `parent` = %s """,(shifts[0].name), as_dict=True)
				if autobreak_setup:
					self.break_hours = 0.00
					self.use_break_hours = 0.00
					for a in autobreak_setup:
						if self.type == "Use":
							if a.from_hrs <= total_hours <= a.to_hrs:
								self.use_break_hours = flt(a.break_mins, 2)/60
								break
						else:
							if a.from_hrs <= total_hours <= a.to_hrs:
								self.break_hours = flt(a.break_mins, 2)/60
								break

	def chk_holiday(self, target_date):
		holiday_tag  = 0
		location = frappe.get_value("Employee", self.employee, "location")

		holiday = frappe.db.sql("""SELECT `name` FROM `tabHoliday` WHERE holiday_date = %s 
			AND company = %s AND location = %s """, (target_date, self.company, location), as_dict=True)

		if holiday:
			holiday_tag = 1

		return holiday_tag

	#FILE CTO
	def file_validate_cto(self):
		if self.type == "File":
			self.file_pre_validate_fields()
			self.file_get_target_date()
			self.file_validate_actual_logs()
			self.file_validate_duplicate()
			self.file_validate_max_filing()
			self.file_process_cto()
			self.file_get_workshift_setup()
			self.file_post_validate_fields()

	def file_pre_validate_fields(self):
		if not self.file_from_date:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> File From Date is required").format(self.name))

		if not self.file_to_date:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> File To Date is required").format(self.name))

	def file_get_target_date(self):
		if self.file_from_date and self.file_to_date:
			self.file_target_date = self.file_from_date
			if self.is_previous:
				self.file_target_date = getdate(self.file_from_date) - timedelta(days=1)

	def file_validate_actual_logs(self):
		from_date, to_date, tc_from_date, tc_to_date, ob_from_date, ob_to_date = None, None, None, None, None, None
		#Get Employee Time In and Time Out
		time_in, time_out = get_current_logs(self.employee, getdate(self.file_target_date))
		if time_in:
			tc_from_date = datetime.strptime(str(time_in), '%Y-%m-%d %H:%M:%S')
		if time_out:
			tc_to_date = datetime.strptime(str(time_out), '%Y-%m-%d %H:%M:%S')

		#Get Employee OB In and OB Out
		obs = get_ob_list(self.employee, getdate(self.file_target_date), getdate(self.file_target_date), getdate(self.file_target_date), 1)
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

		#Process Final Logs
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

		if (not from_date) and (not to_date):
			frappe.throw(_("You have no actual logs for today"))
		if (not from_date) or (not to_date):
			frappe.throw(_("You have incomplete actual logs for today"))

		self.file_actual_in = from_date
		self.file_actual_out = to_date

		return from_date, to_date

	def file_validate_duplicate(self):
		existing_application = frappe.db.sql("""SELECT `name`, `file_from_date`, `file_to_date`, `file_from_time`, `file_to_time` FROM `tabCompensatory Time Off` 
			WHERE `employee` = %s AND `type` = "File" AND `file_target_date` = %s AND `docstatus` = 1 AND `workflow_state` = "Approved" """,( self.employee, self.file_target_date ), as_dict=1)
		if existing_application:
			for d in existing_application:
				existing_from = datetime.strptime(str(d.file_from_date) + ' ' + str(d.file_from_time), '%Y-%m-%d %H:%M:%S')
				existing_to = datetime.strptime(str(d.file_to_date) + ' ' + str(d.file_to_time), '%Y-%m-%d %H:%M:%S')
				
				cur_from = datetime.strptime(str(self.file_from_date) + ' ' + str(self.file_from_time), '%Y-%m-%d %H:%M:%S')
				cur_to = datetime.strptime(str(self.file_to_date) + ' ' + str(self.file_to_time), '%Y-%m-%d %H:%M:%S')

				if existing_from == cur_from and existing_to == cur_to:
					frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Compensatory Time Off Application already exists, {1}").format(self.name, d.name))
				if existing_from < cur_from < existing_to or existing_from < cur_to < existing_to:
					frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Compensatory Time Off Application already exists, {1}").format(self.name, d.name))
				if cur_from < existing_from < cur_to or cur_from < existing_to < cur_to:
					frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Compensatory Time Off Application already exists, {1}").format(self.name, d.name))

	def file_validate_max_filing(self):
		cto_max_filing = frappe.db.sql(""" SELECT `frequency`, `max_count` FROM `tabCompensatory Time Off Max Filing` ORDER BY `frequency` """, as_dict=1)
		if cto_max_filing:
			entry_filing = {}
			from_date = None
			to_date = None

			for mxf in cto_max_filing:
				if mxf.frequency == "Daily":
					from_date = getdate( self.file_target_date )
					to_date = getdate( self.file_target_date )

				if mxf.frequency == "Monthly":
					month = int(datetime.strptime(self.file_target_date, "%Y-%m-%d").month)
					year = int(datetime.strptime(self.file_target_date, "%Y-%m-%d").year)

					from_date = getdate( str(year)+"-"+str(month)+"-01" )
					to_date = getdate( str(year)+"-"+str(month)+"-"+str(calendar.monthrange(int(year), int(month))[1]) )

				if mxf.frequency == "Yearly":
					month = int(datetime.strptime(self.file_target_date, "%Y-%m-%d").month)
					year = int(datetime.strptime(self.file_target_date, "%Y-%m-%d").year)

					from_date = getdate( str(year)+"-01-01" )
					to_date = getdate( str(year)+"-12-"+str(calendar.monthrange(int(year), 12)[1]) )

				if from_date and to_date:
					filed_apps = frappe.db.sql("""SELECT COUNT(*) as filed_count FROM `tabCompensatory Time Off` WHERE `docstatus` != 2 AND `type` = "File" AND `employee` = %s 
						AND `file_target_date` >= %s AND `file_target_date` <= %s """,( self.employee, getdate(from_date), getdate(to_date) ), as_dict=1)
					if filed_apps:
						if int(filed_apps[0].filed_count) > int(mxf.max_count):
							frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Max {1} File Compensatory Time Off is {2}. You already have {3} filed.").format(self.name, mxf.frequency, mxf.max_count, filed_apps[0].filed_count))

	def file_process_cto(self):
		self.get_target_date()
		from_date = datetime.strptime(str(self.file_from_date) + ' ' + str(self.file_from_time), '%Y-%m-%d %H:%M:%S')
		to_date = datetime.strptime(str(self.file_to_date) + ' ' + str(self.file_to_time), '%Y-%m-%d %H:%M:%S')
		actual_from_date, actual_to_date = self.file_validate_actual_logs()
		schedule = get_schedule(self.employee, self.file_target_date, self.file_target_date)

		if not actual_from_date <= from_date <= actual_to_date:
			frappe.throw(_("File From is not within your actual logs"))

		if not actual_from_date <= to_date <= actual_to_date: 
			frappe.throw(_("File To is not within your actual logs"))

		shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0]['work_shift']), as_dict=1)
		#if not shift[0]['cto_allow_file_within_shift'] and (schedule[0]['datetime_out'] > from_date):
		#	from_date = schedule[0]['datetime_out']
		if not shift[0]['cto_allow_file_within_shift'] and not self.chk_holiday(self.file_target_date):
			if datetime.strptime(str(self.file_target_date) + ' ' + str(shift[0].time_in), '%Y-%m-%d %H:%M:%S') < from_date < datetime.strptime(str(self.file_target_date) + ' ' + str(shift[0].time_out), '%Y-%m-%d %H:%M:%S'):
				frappe.throw(_("You cannot file within your shift"))
			if datetime.strptime(str(self.file_target_date) + ' ' + str(shift[0].time_in), '%Y-%m-%d %H:%M:%S') < to_date < datetime.strptime(str(self.file_target_date) + ' ' + str(shift[0].time_out), '%Y-%m-%d %H:%M:%S'):
				frappe.throw(_("You cannot file within your shift"))
			if (schedule[0]['datetime_out'] > from_date):
				from_date = schedule[0]['datetime_out']

		if from_date <= to_date:
			total_hrs = to_date - from_date
		else:
			total_hrs = to_date - from_date + timedelta(days=1)

		total_hours = abs(flt(total_hrs.total_seconds() /60 /60, 2))
		self.get_autobreak_hrs(total_hours)
		total_hours = flt(total_hours, 2) - flt(self.break_hours, 2)
		self.total_hours = flt(total_hours, 2)

		work_hours = 8
		for d in schedule:
			if d['work_hours'] > 0:
				work_hours = flt(d['work_hours'])
			else:
				work_hours = 8

		if work_hours > 0:
			if frappe.db.get_single_value('Timekeeping Settings', 'cto_file_type') == "Day":
				self.credits_earned = flt(self.total_hours,2)/flt(work_hours, 2)
				if self.credits_earned > 1:
					self.credits_earned = 1.0
			else:
				self.credits_earned = flt(self.total_hours,2)/flt(work_hours, 2)

		self.balance = self.credits_earned - self.credits_used

	def file_actual_logs_based_credits(self, from_date, to_date):
		tc_from_date, tc_to_date, ob_from_date, ob_to_date = None, None, None, None

		#Get Employee Time In and Time Out
		time_in, time_out = get_current_logs(self.employee, getdate(self.file_target_date))
		if (time_in) or (time_out):
			tc_from_date = datetime.strptime(str(time_in), '%Y-%m-%d %H:%M:%S')
			tc_to_date = datetime.strptime(str(time_out), '%Y-%m-%d %H:%M:%S')

		#Get Employee OB In and OB Out
		obs = get_ob_list(self.employee, getdate(self.file_target_date), getdate(self.file_target_date), getdate(self.file_target_date), 0)
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

		#Process Final Logs
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

		if not from_date and not to_date:
			return frappe.throw(_("You don't have actual logs on your filed CTO."))

		self.file_from_date = from_date.date()
		self.file_to_date = to_date.date()
		self.file_from_time = str(from_date.time())
		self.file_to_time = str(to_date.time())

		return from_date, to_date			

	def file_get_workshift_setup(self):
		schedule = get_schedule(self.employee, self.file_target_date, self.file_target_date)
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

	def file_post_validate_fields(self):
		if self.credits_earned <= 0:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Credits Earned must be greater than 0").format(self.name))

	def file_cancel_cto(self):
		if self.type == "File":
			filed_cto = frappe.db.sql(""" SELECT `parent` FROM `tabCompensatory Time Off Table` WHERE `filed_cto` = %s """,( self.name ), as_dict=1)
			if filed_cto:
				for d in filed_cto:
					frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Cannot cancel because CTO Application {1} is linked with CTO Application {2}").format(self.name, self.name, d.parent))

	#USE CTO
	def use_validate_cto(self):
		if self.type == "Use":
			self.use_pre_validate_fields()
			self.use_get_target_date()
			self.use_process_cto()
			self.use_validate_date()
			self.validate_use_credits()
			self.use_get_workshift_setup()
			self.validate_required_credits()

	def use_pre_validate_fields(self):
		if not self.use_from_date:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Use From Date is required").format(self.name))

		if not self.use_to_date:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Use To Date is required").format(self.name))

		if frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type') == "Day":
			if not self.filed_cto:
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Filed CTO is required").format(self.name))

	def use_get_target_date(self):
		if self.use_from_date and self.use_to_date:
			self.use_target_date = self.use_from_date
			if self.is_previous:
				self.use_target_date = getdate(self.use_from_date) - timedelta(days=1)

	def use_process_cto(self):
		self.get_target_date()
		from_date = datetime.strptime(str(self.use_from_date) + ' ' + str(self.use_fromtime), '%Y-%m-%d %H:%M:%S')
		to_date = datetime.strptime(str(self.use_to_date) + ' ' + str(self.use_totime), '%Y-%m-%d %H:%M:%S')
		if from_date <= to_date:
			total_hrs = to_date - from_date
		else:
			total_hrs = to_date - from_date + timedelta(days=1)

		total_hours = abs(flt(total_hrs.total_seconds() /60 /60, 2))
		self.get_autobreak_hrs(total_hours)
		total_hours = flt(total_hours, 2) - flt(self.use_break_hours, 2)
		self.use_total_hours = total_hours

		work_hours = 8
		schedule = get_schedule(self.employee, self.use_target_date, self.use_target_date)
		if schedule:
			for d in schedule:
				if d['work_hours'] > 0:
					work_hours = flt(d['work_hours'])
				else:
					work_hours = 8

		if work_hours > 0:
			self.required_credits = flt(total_hours,2)/flt(work_hours, 2)

		total_credits_earned = 0.00
		date_list = []
		last_date = None
		
		cto_validity = frappe.db.get_single_value('Timekeeping Settings', 'cto_validity')
		cto_use_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_validity > 0:
			cto_validity_condition = " AND (%(use_date)s BETWEEN `file_target_date` AND DATE_SUB(`file_target_date`, INTERVAL -"+str(int(cto_validity))+" DAY)) "
		else:
			cto_validity_condition = ""

		if cto_use_type == "Day":
			current_credits = frappe.db.sql("""SELECT credits_earned - credits_used as cred_balance, `file_target_date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %(employee)s AND `docstatus` = 1 AND `workflow_state` = "Approved" AND `name` = %(filed_cto)s AND `balance` > 0 {conditions} """.format(conditions=cto_validity_condition),{
				"employee": self.employee,
				"filed_cto": self.filed_cto,
				"use_date": getdate(self.use_target_date),
				"cto_validity": cto_validity,
			}, as_dict=True)
		else:
			current_credits = frappe.db.sql("""SELECT credits_earned - credits_used as cred_balance, `file_target_date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %(employee)s AND `docstatus` = 1 AND `workflow_state` = 'Approved' AND `balance` > 0 AND `file_target_date` <= %(use_date)s {conditions} ORDER BY `file_target_date` ASC """.format(conditions=cto_validity_condition),{
				"employee": self.employee,
				"use_date": getdate(self.use_target_date),
				"cto_validity": cto_validity,
			}, as_dict=True)

		if current_credits:
			for d in current_credits:
				total_credits_earned += d.cred_balance
				date_list.append(d.file_target_date)

			last_date = date_list[-1]

		self.total_credits_earned = total_credits_earned
		
		return last_date

	def use_validate_date(self):
		last_date = self.use_process_cto()
		if last_date:
			if getdate(self.use_target_date) < getdate(last_date):
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Insufficient Balance").format(self.name))

	def validate_use_credits(self):
		if flt(self.required_credits, 2) > flt(self.total_credits_earned, 2):
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> You dont have enough credits").format(self.name))

	def use_get_workshift_setup(self):
		schedule = get_schedule(self.employee, self.use_target_date, self.use_target_date)
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

	def validate_required_credits(self):
		if self.required_credits <= 0:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Required Credits must be greater than 0").format(self.name))

	def use_deduct_cto(self):
		if self.type == "Use":
			entries = [] 
			req_credits = self.required_credits

			cto_validity = frappe.db.get_single_value('Timekeeping Settings', 'cto_validity')
			cto_use_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
			if cto_validity > 0:
				cto_validity_condition = " AND (%(use_date)s BETWEEN `file_target_date` AND DATE_SUB(`file_target_date`, INTERVAL -"+str(int(cto_validity))+" DAY)) "
			else:
				cto_validity_condition = ""

			if cto_use_type == "Day":
				filed_cto = frappe.db.sql("""SELECT `name`, `credits_earned`, credits_used, balance, `file_target_date` FROM `tabCompensatory Time Off` 
					WHERE `type` = "File" AND `employee` = %(employee)s AND `docstatus` = 1 AND `workflow_state` = "Approved" AND `name` = %(filed_cto)s AND `balance` > 0 {conditions} """.format(conditions=cto_validity_condition),{
					"employee": self.employee,
					"filed_cto": self.filed_cto,
					"use_date": getdate(self.use_target_date),
					"cto_validity": cto_validity,
					}, as_dict=True)
			else:
				filed_cto = frappe.db.sql("""SELECT `name`, `credits_earned`, credits_used, balance, `file_target_date` FROM `tabCompensatory Time Off` 
					WHERE `type` = "File" AND `employee` = %(employee)s AND `docstatus` = 1 AND `workflow_state` = "Approved" AND `balance` > 0 {conditions} ORDER BY `file_target_date` ASC""".format(conditions=cto_validity_condition),{
					"employee": self.employee,
					"use_date": getdate(self.use_target_date),
					"cto_validity": cto_validity,
					}, as_dict=True)

			if filed_cto:
				#Validate credits
				fc_credits_earned = 0.00
				for fc in filed_cto:
					fc_credits_earned += fc.balance
				if flt(fc_credits_earned, 2) < flt(req_credits, 2):
					frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> You dont have enough credits").format(self.name))
				#Map CTO
				for a in filed_cto:
					if req_credits > 0: 
						cred_used = 0
						deduct = 0
						if a.balance > 0:
							if flt(a.balance) >= flt(req_credits):
								remain_bal = a.balance - req_credits
								cred_used = req_credits
								req_credits = req_credits - cred_used
							else:
								remain_bal = 0.00
								cred_used = a.balance
								req_credits = req_credits - cred_used
							
							row = {
								"filed_cto": a.name,
								"date": a.file_target_date,
								"balance": a.balance,
								"credits_used": cred_used,
								"forfeited_balance": 0,
							}
							
							deduct = flt(a.credits_used)+flt(cred_used)
							if cto_use_type == "Day":
								row['forfeited_balance'] = a.balance - deduct
								deduct = flt(a.balance)
							
							entries.append(row);
							frappe.db.sql(""" UPDATE `tabCompensatory Time Off` SET `credits_used` = %s WHERE `name` = %s """,( deduct, a.name))
							frappe.db.sql(""" UPDATE `tabCompensatory Time Off` SET `balance` = credits_earned-credits_used WHERE `name` = %s """,(a.name))
							frappe.db.commit()
					else:
						break

				for d in entries:
					row = self.append('use_cto_table', {})
					row.update(d)
					row.save(d)
			else:
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> You dont have enough credits").format(self.name))

	def use_validate_deduct(self):
		req_credits = self.required_credits

		cto_validity = frappe.db.get_single_value('Timekeeping Settings', 'cto_validity')
		cto_use_type = frappe.db.get_single_value('Timekeeping Settings', 'cto_use_type')
		if cto_validity > 0:
			cto_validity_condition = " AND (%(use_date)s BETWEEN `file_target_date` AND DATE_SUB(`file_target_date`, INTERVAL -"+str(int(cto_validity))+" DAY)) "
		else:
			cto_validity_condition = ""

		if cto_use_type == "Day":
			filed_cto = frappe.db.sql("""SELECT `name`, `credits_earned`, credits_used, balance, `file_target_date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %(employee)s AND `docstatus` = 1 AND `workflow_state` = "Approved" AND `name` = %(filed_cto)s AND `balance` > 0 {conditions} """.format(conditions=cto_validity_condition),{
				"employee": self.employee,
				"filed_cto": self.filed_cto,
				"use_date": getdate(self.use_target_date),
				"cto_validity": cto_validity,
				}, as_dict=True)
		else:
			filed_cto = frappe.db.sql("""SELECT `name`, `credits_earned`, credits_used, balance, `file_target_date` FROM `tabCompensatory Time Off` 
				WHERE `type` = "File" AND `employee` = %(employee)s AND `docstatus` = 1 AND `workflow_state` = "Approved" AND `balance` > 0 {conditions} ORDER BY `file_target_date` ASC""".format(conditions=cto_validity_condition),{
				"employee": self.employee,
				"use_date": getdate(self.use_target_date),
				"cto_validity": cto_validity,
				}, as_dict=True)

		if filed_cto:
			#Validate credits
			fc_credits_earned = 0.00
			for fc in filed_cto:
				fc_credits_earned += fc.balance
			if flt(fc_credits_earned, 2) < flt(req_credits, 2):
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> You dont have enough credits").format(self.name))

	#Cancel Use CTO
	def revert_credit_deductions(self):
		if self.type == "Use":
			if self.get('use_cto_table'):
				for a in self.get('use_cto_table'):
					revert_credit = a.credits_used
					if a.forfeited_balance:
						revert_credit += a.forfeited_balance

					frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET credits_used = credits_used - %s WHERE `name` = %s AND docstatus = 1 AND `workflow_state` = "Approved" """, (revert_credit, a.filed_cto))
					frappe.db.commit()

					frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET `balance` = (credits_earned - credits_used) WHERE `name` = %s AND docstatus = 1 AND `workflow_state` = "Approved" """, (a.filed_cto))
					frappe.db.commit()

					frappe.db.sql(""" DELETE FROM `tabCompensatory Time Off Table` WHERE filed_cto = %s AND `date` = %s AND docstatus = 1 """, (a.filed_cto, a.date))
					frappe.db.commit()