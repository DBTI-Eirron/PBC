# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, calendar, json
from datetime import date, datetime, timedelta
from frappe import _
from frappe.utils import nowdate, get_time, flt, getdate, get_datetime, cstr
from frappe.model.document import Document
from workwise.time_keeping.attendance_utils import get_schedule, get_ob_list
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs
from workwise.time_keeping.application_utils import ( grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, get_overrides, change_owner, get_levelled_approval, 
	get_levelled_approval_rejection, clear_approval_history, validate_inactive_employee, get_approver_email_list, get_cancelled_by_and_date, get_current_logs, validate_approver_userperm, validate_cutoff_approval_date, get_employee_details)

class CompensatoryTimeOff(Document):
	def validate(self):
		get_employee_details(self)
		validate_inactive_employee(self)
		clear_approval_history(self)
		grant_head_subordinate_access(self)
		self.js_table_events()
		self.validate_child_table()
		self.validate_cto_sumary()
		change_owner(self)

	def on_update(self):
		validate_reject_cancel_own_application(self)

	def before_submit(self):
		validate_approve_own_application(self)
		if not frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers'):
			if self.cto_targets and self.type == 'Use':
				for d in self.cto_targets:
					self.use_deduct_cto(required_credits=d.required_credits, filed_cto=d.filed_cto, target_date=d.target_date, employee=self.employee)

	def on_submit(self):
		get_approver_and_date(self)
		get_approver_email_list(self, 'on_submit')
		#validate_approver_userperm(self)
		validate_cutoff_approval_date(self)

	def before_update_after_submit(self):
		if self.cto_targets:
			for d in self.cto_targets:
				validate_strict_cto(target_date=d.target_date, employee=self.employee, from_time=d.from_time, to_time=d.to_time)
				if frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers') and self.type == 'Use':
					use_validate_cto(employee=self.employee, filed_cto=d.filed_cto, target_date=d.target_date, application_name=self.name, type=self.type, required_credits=d.required_credits, credits_earned=d.credits_earned, total_hours=d.cto_hours)
		get_approver_email_list(self, 'before_update_after_submit')
		get_levelled_approval(self)
		#validate_approver_userperm(self)
		validate_cutoff_approval_date(self)
		if self.workflow_state == "Approved":
			if frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers'):
				if self.cto_targets and self.type == 'Use':
					for d in self.cto_targets:
						self.use_deduct_cto(required_credits=d.required_credits, filed_cto=d.filed_cto, target_date=d.target_date, employee=self.employee)

	def before_cancel(self):
		self.file_cancel_cto()
		self.revert_credit_deductions()
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		get_cancelled_by_and_date(self)

	def validate_cto_sumary(self):
		if self.type == "File":
			if not self.total_credits_earned:
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> No Credits Earned").format(self.name))

			if not self.total_hours:
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> No Total Hours").format(self.name))

		if self.type == "Use":
			if self.total_credits_earned < self.total_required_credits:
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Not enough Credits Earned").format(self.name))

	def validate_child_table(self):
		if self.cto_targets:
			validations = []
			for d in self.cto_targets:
				if self.type == "File":
					fval_result = file_validate_actual_logs(employee=self.employee, target_date=d.target_date)
					d.actual_in = fval_result['actual_in']
					d.actual_out = fval_result['actual_out']
					validations.extend( fval_result['validations'] )
					
					file_validate_duplicate(employee=self.employee, from_date=d.from_date, from_time=d.from_time, to_date=d.to_date, to_time=d.to_time, application_name=self.name)
					file_validate_max_filing(target_date=d.target_date, employee=self.employee, application_name=self.name)
					fvc_result = file_validate_cto(from_date=d.from_date, from_time=d.from_time, to_date=d.to_date, to_time=d.to_time, actual_in=d.actual_in, actual_out=d.actual_out, employee=self.employee, 
						target_date=d.target_date, type=self.type, total_hours=d.cto_hours, application_name=self.name, credits_earned=d.credits_earned, company=self.company)
					validations.extend( fvc_result )

				if self.type == "Use":
					if frappe.db.get_single_value('Timekeeping Settings', 'cto_forfeit') and not d.filed_cto:
						frappe.throw(_("<balance>Compensatory Time Off: {0}</b><hr> Filed CTO for date {1} is required").format(self.name, d.target_date))
					file_validate_duplicate(employee=self.employee, from_date=d.from_date, from_time=d.from_time, to_date=d.to_date, to_time=d.to_time, application_name=self.name)
					use_validate_cto(employee=self.employee, filed_cto=d.filed_cto, target_date=d.target_date, application_name=self.name, 
						type=self.type, required_credits=d.required_credits, credits_earned=d.credits_earned, total_hours=d.cto_hours)
				validate_strict_cto(target_date=d.target_date, employee=self.employee, from_time=d.from_time, to_time=d.to_time)
			prompt_validation_messages(validations)
	
	def js_events(self):
		#Generate Target Dates
		if self.type and self.from_date and self.to_date and self.from_time and self.to_time:
			entries = {
				'from_date': self.from_date,
				'to_date': self.to_date,
				'from_time': self.from_time,
				'to_time': self.to_time,
			}
			target_dates = generate_target_dates(**entries)
			self.set('cto_targets', [])
			for d in target_dates:
				row = self.append('cto_targets', {})
				row.update(d)
			self.js_table_events()

	def js_table_events(self):
		table_rows = []
		included_cto_credits = []
		total_credits_earned = 0
		
		if self.cto_targets:
			validations = []
			for d in self.cto_targets:
				total_credits_earned = 0
				from_datetime = None
				to_datetime = None
				#Validate Date
				if d.from_date and d.from_time and d.to_date and d.to_time:
					from_datetime = datetime.strptime(str(d.from_date) + ' ' + str(d.from_time), '%Y-%m-%d %H:%M:%S')
					to_datetime = datetime.strptime(str(d.to_date) + ' ' + str(d.to_time), '%Y-%m-%d %H:%M:%S')
		
				if from_datetime > to_datetime:
					frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> File From must be less than File To").format(self.name))

				#Get data
				d.target_date = get_target_date(from_date=d.from_date, is_previous=d.is_previous)
				d.cto_hours = get_cto_hours(from_date=d.from_date, to_date=d.to_date, from_time=d.from_time, to_time=d.to_time)
				d.break_hours = self.get_autobreak_hrs(employee=self.employee, target_date=d.target_date, cto_hours=d.cto_hours)
				d.cto_hours = d.cto_hours - d.break_hours

				if self.type == 'File':
					d.credits_earned = d.cto_hours
					d.balance = flt(d.credits_earned) - flt(d.credits_used)

				if self.type == 'Use':
					d.required_credits = flt(d.cto_hours, 2)
					if d.filed_cto:
						validate_filed_cto(filed_cto=d.filed_cto, target_date=d.target_date, employee=self.employee)
					d.credits_earned, last_earned_date, cto_credits = get_total_credits_earned(employee=self.employee, filed_cto=d.filed_cto, target_date=d.target_date, included_cto_credits=included_cto_credits)
					total_credits_earned += cto_credits

				table_rows.append({
					'credits_earned': d.credits_earned,
					'required_credits': d.required_credits,
					'credits_used': d.credits_used,
					'balance': d.balance,
					'break_hours': d.break_hours,
					'cto_hours': d.cto_hours,
					'total_credits_earned': total_credits_earned
				})
			prompt_validation_messages(validations)

		table_summary = get_table_summary(rows=table_rows, type=self.type)
		self.total_credits_earned = table_summary['total_credits_earned']
		self.total_required_credits = table_summary['total_required_credits']
		self.total_credits_used = table_summary['total_credits_used']
		self.total_balance = table_summary['total_balance']
		self.total_break_hours = table_summary['total_break_hours']
		self.total_hours = table_summary['total_hours']

	def cto_forfeit_status(self):
		result = 1
		if frappe.db.get_single_value('Timekeeping Settings', 'cto_forfeit'):
			result = 0
		return result

	def get_autobreak_hrs(self, **entry):
		schedule, shifts, autobreak_setup = None, None, None
		break_hours = 0
		if self.is_new():
			if not self.amended_from:
				if not break_hours:
					break_hours = 0

		schedule = get_schedule(entry['employee'], entry['target_date'], entry['target_date'])	
		if schedule:
			shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0]['work_shift']), as_dict=True)

		if shifts:
			autobreak_setup = frappe.db.sql("""SELECT break_mins, from_hrs, to_hrs FROM `tabCTO Auto Break Table` 
				WHERE `parenttype` = "Work Shift" AND `parent` = %s """,(shifts[0].name), as_dict=True)

		if autobreak_setup:
			break_hours = 0
			for a in autobreak_setup:
				if flt(a.from_hrs) <= flt(entry['cto_hours']) <= flt(a.to_hrs):
					break_hours = flt(a.break_mins, 2)/60
					break

		return break_hours

	def use_deduct_cto(self, **entry):
		entries = [] 
		req_credits = entry['required_credits']

		current_credits_condition = ""
		cto_forfeit = frappe.db.get_single_value('Timekeeping Settings', 'cto_forfeit')
		if cto_forfeit:
			current_credits_condition += " AND CTO.`name`='{0}' ".format(entry['filed_cto'])

		cto_validity = frappe.db.get_single_value('Timekeeping Settings', 'cto_validity')
		if cto_validity > 0:
			current_credits_condition += " AND ('{0}' BETWEEN CTT.`target_date` AND DATE_SUB(CTT.`target_date`, INTERVAL -"+str(int(cto_validity))+" DAY)) ".format(str(getdate(entry['target_date'])))

		cto_zero_out = frappe.db.get_single_value('Timekeeping Settings', 'cto_zero_out')
		if cto_zero_out:
			nowyear = datetime.strptime(str(entry['target_date']), '%Y-%m-%d').year
			year_start = getdate(cstr(nowyear)+'-01-'+'01')
			year_end = getdate(cstr(nowyear)+'-12-'+'31')
			cto_validity_condition += " AND (CTT.`target_date` BETWEEN '{0}' AND '{1}') ".format(cstr(year_start), cstr(year_end))

		filed_cto = frappe.db.sql(""" SELECT CTT.`credits_earned` - CTT.`credits_used` as balance, CTT.`target_date`, CTT.`name`, 
			CTT.`credits_earned`, CTT.`credits_used`, CTT.`target_date`, CTT.`parent`
			FROM `tabCompensatory Time Off Targets` CTT INNER JOIN `tabCompensatory Time Off` CTO ON CTT.`parent`=CTO.`name`
			WHERE CTO.`type`="File" AND CTO.`employee`=%(employee)s AND CTO.`docstatus` = 1 AND CTO.`workflow_state` = "Approved"
			AND ((CTT.`credits_earned`-CTT.`credits_used`) > 0) {conditions} ORDER BY CTT.`target_date` ASC """.format(conditions=current_credits_condition),{
			"employee": entry['employee'],
		}, as_dict=True)

		if filed_cto:
			update_cto_table_list = []
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
						if a.balance >= flt(req_credits):
							remain_bal = a.balance - req_credits
							cred_used = req_credits
							req_credits = req_credits - cred_used
						else:
							remain_bal = 0.00
							cred_used = a.balance
							req_credits = req_credits - cred_used
						
						row = {
							"filed_cto": a.parent,
							"cto_target": a.name,
							"date": a.target_date,
							"balance": a.balance,
							"credits_used": cred_used,
							"forfeited_balance": 0,
						}

						deduct = a.credits_used + cred_used
						if cto_forfeit:
							if a.balance >= flt(req_credits):
								row['forfeited_balance'] = a.balance - cred_used
							else:
								row['forfeited_balance'] = a.balance - deduct

							if row['forfeited_balance'] <= 0:
								row['forfeited_balance'] = 0
							deduct += row['forfeited_balance']
						
						entries.append(row)
						ctof = frappe.db.sql(""" SELECT `credits_earned`-`credits_used` as balance, `credits_used`, `parent` FROM `tabCompensatory Time Off Targets` WHERE `name` = %s """,(a.name), as_dict=1)
						ctof_cred_used, ctof_bal = 0, 0
						for f in ctof:
							ctof_cred_used = deduct
							ctof_bal = f.balance - (f.credits_used + deduct)
							if ctof_bal < 0:
								ctof_bal = 0
						frappe.db.sql(""" UPDATE `tabCompensatory Time Off Targets` SET `credits_used` = %s, `balance`=`credits_earned`-%s WHERE `name` = %s """,( ctof_cred_used, ctof_cred_used, a.name))
						update_cto_table_list.append(a.parent)
						#frappe.db.sql(""" UPDATE `tabCompensatory Time Off Targets` SET `balance` = `credits_earned`-`credits_used` WHERE `name` = %s """,(a.name))
						#frappe.db.commit()
				else:
					break

				if update_cto_table_list:
					update_cto_table_summary(update_cto_table_list, self.type)

			for d in entries:
				row = self.append('use_cto_table', {})
				row.update(d)
		else:
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> You dont have enough credits").format(self.name))

	def file_cancel_cto(self):
		if self.type == "File":
			for d in self.cto_targets:
				filed_cto = frappe.db.sql(""" SELECT `parent` FROM `tabCompensatory Time Off Table` WHERE `cto_target` = %s """,( d.name ), as_dict=1)
				if filed_cto:
					for d in filed_cto:
						frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Cannot cancel because CTO Application {1} is linked with CTO Application {2}").format(self.name, self.name, d.parent))

	def revert_credit_deductions(self):
		if self.type == "Use":
			update_cto_table_list = []
			if self.get('use_cto_table'):
				for a in self.get('use_cto_table'):
					update_cto_table_list.append(a.filed_cto)
					revert_credit = a.credits_used
					if a.forfeited_balance > 0:
						revert_credit += a.forfeited_balance

					frappe.db.sql("""UPDATE `tabCompensatory Time Off Targets` SET credits_used = credits_used - %s WHERE `name` = %s AND docstatus = 1 """, (revert_credit, a.cto_target))
					frappe.db.commit()

					frappe.db.sql("""UPDATE `tabCompensatory Time Off Targets` SET `balance` = (credits_earned - credits_used) WHERE `name` = %s AND docstatus = 1 """, (a.cto_target))
					frappe.db.commit()
			#self.db_set("use_cto_table", None)
			self.use_cto_table = []

			if update_cto_table_list:
				update_cto_table_summary(update_cto_table_list, self.type)

@frappe.whitelist()
def generate_target_dates(**entry):
	entries = []
	dates = []
	target_table = []

	start = datetime.strptime(str(entry['from_date']), '%Y-%m-%d')
	end = datetime.strptime(str(entry['to_date']), '%Y-%m-%d')
	step = timedelta(days=1)

	if (end-start).days <= 30:
		while start <= end:
			dates.append(start.date());
			start += step
	else:
		frappe.throw(_( "You can only file Maximum of 30 Days in One Application" ))

	for i in dates:
		info = {
			"target_date": i,
			"from_date": i,
			"to_date": i,
			"from_time": entry['from_time'],
			"to_time": entry['to_time'],
			"is_previous": 0,
		}

		target_table.append(info);

	entries = sorted(list(target_table), key=lambda k: k['target_date'])

	return entries

def get_target_date(**entry):
	target_date = getdate(entry['from_date'])
	if entry['is_previous']:
		target_date = getdate(entry['from_date']) - timedelta(days=1)

	return target_date

def get_cto_hours(**entry):
	total_hrs = 0
	from_date = datetime.strptime(str(entry['from_date']) + ' ' + str(entry['from_time']), '%Y-%m-%d %H:%M:%S')
	to_date = datetime.strptime(str(entry['to_date']) + ' ' + str(entry['to_time']), '%Y-%m-%d %H:%M:%S')
	if from_date <= to_date:
		total_hrs = (to_date - from_date).total_seconds() / 60 / 60

	return total_hrs

def get_total_credits_earned(**entry):
	credits_earned = 0
	total_credits_earned = 0
	date_list = []
	last_date = None
	
	current_credits_condition = ""
	cto_forfeit = frappe.db.get_single_value('Timekeeping Settings', 'cto_forfeit')
	if cto_forfeit:
		current_credits_condition += " AND CTO.`name`='{0}' ".format(entry['filed_cto'])

	cto_validity = frappe.db.get_single_value('Timekeeping Settings', 'cto_validity')
	if cto_validity > 0:
		current_credits_condition += " AND ('{0}' BETWEEN CTT.`target_date` AND DATE_SUB(CTT.`target_date`, INTERVAL -"+str(int(cto_validity))+" DAY)) ".format(str(getdate(entry['target_date'])))

	cto_zero_out = frappe.db.get_single_value('Timekeeping Settings', 'cto_zero_out')
	if cto_zero_out:
		nowyear = datetime.strptime(str(entry['target_date']), '%Y-%m-%d').year
		year_start = getdate(cstr(nowyear)+'-01-'+'01')
		year_end = getdate(cstr(nowyear)+'-12-'+'31')
		current_credits_condition += " AND (CTT.`target_date` BETWEEN '{0}' AND '{1}') ".format(cstr(year_start), cstr(year_end))

	current_credits = frappe.db.sql(""" SELECT CTT.`name`, CTT.`credits_earned` - CTT.`credits_used` as cred_balance, CTT.`target_date` 
		FROM `tabCompensatory Time Off Targets` CTT JOIN `tabCompensatory Time Off` CTO ON CTT.`parent`=CTO.`name`
		WHERE CTO.`type`="File" AND CTO.`employee`=%(employee)s AND CTO.`docstatus` = 1 AND CTO.`workflow_state` = "Approved"
		AND ((CTT.`credits_earned`-CTT.`credits_used`) > 0) AND CTT.`target_date` <= %(target_date)s {conditions} ORDER BY CTT.`target_date` ASC """.format(conditions=current_credits_condition),{
		"employee": entry['employee'],
		"target_date": getdate(entry['target_date']),
	}, as_dict=True)

	if current_credits:
		for d in current_credits:
			credits_earned += d.cred_balance
			if 'included_cto_credits' in entry:
				if d.name not in entry['included_cto_credits']:
					total_credits_earned += d.cred_balance
					entry['included_cto_credits'].append(d.name)
			date_list.append(d.file_target_date)
		last_date = date_list[-1]

	if 'included_cto_credits' in entry:
		return credits_earned, last_date, total_credits_earned
	else:
		return credits_earned, last_date

def file_validate_actual_logs(**entry):
	result = {}
	from_date, to_date, tc_from_date, tc_to_date, ob_from_date, ob_to_date = None, None, None, None, None, None
	validations = []
	time_in_list = []
	time_out_list = []

	#Get Employee Time In and Time Out
	time_in, time_out = get_current_logs(entry['employee'], getdate(entry['target_date']))
	if time_in:
		tc_from_date = datetime.strptime(str(time_in), '%Y-%m-%d %H:%M:%S')
		time_in_list.append( get_datetime(tc_from_date) )
	if time_out:
		tc_to_date = datetime.strptime(str(time_out), '%Y-%m-%d %H:%M:%S')
		time_out_list.append( get_datetime(tc_to_date) )

	#Get Employee OB In and OB Out
	obs = get_ob_list(entry['employee'], getdate(entry['target_date']), getdate(entry['target_date']), getdate(entry['target_date']), 1)
	for ob in obs:
		if ob_from_date:
			if datetime.strptime(str(ob.target_date) + ' ' + str(ob.from_time), '%Y-%m-%d %H:%M:%S') < ob_from_date:
				ob_from_date = datetime.strptime(str(ob.target_date) + ' ' + str(ob.from_time), '%Y-%m-%d %H:%M:%S')
		else:
			ob_from_date = datetime.strptime(str(ob.target_date) + ' ' + str(ob.from_time), '%Y-%m-%d %H:%M:%S')
		time_in_list.append( get_datetime(ob_from_date) )

		if ob_to_date:
			if datetime.strptime(str(ob.to_date) + ' ' + str(ob.to_time), '%Y-%m-%d %H:%M:%S') > ob_to_date:
				ob_to_date = datetime.strptime(str(ob.to_date) + ' ' + str(ob.to_time), '%Y-%m-%d %H:%M:%S')
		else:
			ob_to_date = datetime.strptime(str(ob.to_date) + ' ' + str(ob.to_time), '%Y-%m-%d %H:%M:%S')
		time_out_list.append( get_datetime(ob_to_date) )

	#Get Overrides
	timelogs_list = get_overrides(entry['employee'], getdate(entry['target_date']), getdate(entry['target_date']))
	for tl in timelogs_list:
		if tl.time_in:
			time_in_list.append(get_datetime(tl.time_in))
		if tl.time_out:
			time_out_list.append(get_datetime(tl.time_out))

	#Process Final Logs
	if time_in_list:
		from_date = min(time_in_list)
	if time_out_list:
		to_date = max(time_out_list)

	if (not from_date) and (not to_date):
		validations.append({
			'validation': 'No Actual Logs',
			'target_date': getdate(entry['target_date']),
		})
	if (not from_date) or (not to_date):
		validations.append({
			'validation': 'Incomplete Actual Logs',
			'target_date': getdate(entry['target_date']),
		})

	result['actual_in'] = get_datetime(from_date)
	result['actual_out'] = get_datetime(to_date)
	result['validations'] = validations

	return result

def file_validate_duplicate(**entry):
	existing_application = frappe.db.sql("""SELECT CTO.`name`, CTT.`target_date`, CTT.`from_date`, CTT.`from_time`, CTT.`to_date`, CTT.`to_time`
		FROM `tabCompensatory Time Off Targets` CTT JOIN `tabCompensatory Time Off` CTO ON CTO.`name`=CTT.`parent`
		WHERE CTO.`employee` = %s AND CTO.`docstatus` = 1 AND CTO.`workflow_state` = "Approved" """,( entry['employee'] ), as_dict=1)

	if existing_application:
		for d in existing_application:
			existing_from = datetime.strptime(str(d.from_date) + ' ' + str(d.from_time), '%Y-%m-%d %H:%M:%S')
			existing_to = datetime.strptime(str(d.to_date) + ' ' + str(d.to_time), '%Y-%m-%d %H:%M:%S')

			cur_from = datetime.strptime(str(entry['from_date']) + ' ' + str(entry['from_time']), '%Y-%m-%d %H:%M:%S')
			cur_to = datetime.strptime(str(entry['to_date']) + ' ' + str(entry['to_time']), '%Y-%m-%d %H:%M:%S')

			if existing_from == cur_from and existing_to == cur_to:
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Compensatory Time Off Application already exists, {1}").format(entry['application_name'], d.name))
			if existing_from < cur_from < existing_to or existing_from < cur_to < existing_to:
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Compensatory Time Off Application already exists, {1}").format(entry['application_name'], d.name))
			if cur_from < existing_from < cur_to or cur_from < existing_to < cur_to:
				frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Compensatory Time Off Application already exists, {1}").format(entry['application_name'], d.name))

def file_validate_max_filing(**entry):
	cto_max_filing = frappe.db.sql(""" SELECT `frequency`, `max_count` FROM `tabCompensatory Time Off Max Filing` ORDER BY `frequency` """, as_dict=1)
	if cto_max_filing:
		entry_filing = {}
		from_date = None
		to_date = None

		for mxf in cto_max_filing:
			if mxf.frequency == "Daily":
				from_date = getdate( entry['target_date'] )
				to_date = getdate( entry['target_date'] )

			if mxf.frequency == "Monthly":
				month = int(datetime.strptime(entry['target_date'], "%Y-%m-%d").month)
				year = int(datetime.strptime(entry['target_date'], "%Y-%m-%d").year)

				from_date = getdate( str(year)+"-"+str(month)+"-01" )
				to_date = getdate( str(year)+"-"+str(month)+"-"+str(calendar.monthrange(int(year), int(month))[1]) )

			if mxf.frequency == "Yearly":
				month = int(datetime.strptime(str(entry['target_date']), "%Y-%m-%d").month)
				year = int(datetime.strptime(str(entry['target_date']), "%Y-%m-%d").year)

				from_date = getdate( str(year)+"-01-01" )
				to_date = getdate( str(year)+"-12-"+str(calendar.monthrange(int(year), 12)[1]) )

			if from_date and to_date:
				filed_apps = frappe.db.sql("""SELECT COUNT(*) as filed_count FROM `tabCompensatory Time Off Targets` CTT JOIN `tabCompensatory Time Off` CTO ON CTT.`parent`=CTO.`name` 
					WHERE CTO.`docstatus` != 2 AND CTO.`type` = "File" AND CTO.`employee` = %s AND CTT.`target_date` >= %s 
					AND CTT.`target_date` <= %s """,( entry['employee'], getdate(from_date), getdate(to_date) ), as_dict=1)
				if filed_apps:
					if int(filed_apps[0].filed_count) > int(mxf.max_count):
						frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Max {1} File Compensatory Time Off is {2}. You already have {3} filed.").format(entry['application_name'], mxf.frequency, mxf.max_count, filed_apps[0].filed_count))

def file_validate_cto(**entry):
	validations = []
	from_date = datetime.strptime(str(entry['from_date']) + ' ' + str(entry['from_time']), '%Y-%m-%d %H:%M:%S')
	to_date = datetime.strptime(str(entry['to_date']) + ' ' + str(entry['to_time']), '%Y-%m-%d %H:%M:%S')
	actual_from_date = entry['actual_in']
	actual_to_date = entry['actual_out']

	schedule = get_schedule(entry['employee'], entry['target_date'], entry['target_date'])
	if schedule:
		shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0]['work_shift']), as_dict=1)

		if shift[0]['cto_allow_file_within_shift'] < 1 and not chk_holiday(entry['employee'], entry['company'], entry['target_date']):
			shift_from = datetime.strptime(str(entry['target_date']) + ' ' + str(shift[0].time_in), '%Y-%m-%d %H:%M:%S')
			shift_to = datetime.strptime(str(entry['target_date']) + ' ' + str(shift[0].time_out), '%Y-%m-%d %H:%M:%S')

			if (shift_from < from_date < shift_to) or (shift_from < to_date < shift_to):
				frappe.throw(_("You cannot file within your shift"))
			if (from_date < shift_from < to_date) or  (from_date < shift_to < to_date):
				frappe.throw(_("You cannot file within your shift"))
			if shift_from == from_date and to_date == shift_to: 
				frappe.throw(_("You cannot file within your shift"))
			#if (schedule[0]['datetime_out'] > from_date):
			#	from_date = schedule[0]['datetime_out']
			
		if not (actual_from_date <= from_date <= actual_to_date):
			validations.append({
				'validation': 'File From is not within your actual logs',
				'target_date': entry['target_date'],
			})

		if not (actual_from_date <= to_date <= actual_to_date):
			validations.append({
				'validation': 'File To is not within your actual logs',
				'target_date': entry['target_date'],
			})

		if entry['type'] == "File":
			if shift[0].cto_min_filing_hrs > 0:
				if entry['total_hours'] < int(shift[0].cto_min_filing_hrs):
					frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Minimum hours of filing is {1}").format(entry['application_name'], shift[0].cto_min_filing_hrs))
			if shift[0].cto_max_filing_hrs > 0:
				if entry['total_hours'] > int(shift[0].cto_max_filing_hrs):
					frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Maximum hours of filing is {1}").format(entry['application_name'], shift[0].cto_max_filing_hrs))
	else:
		frappe.throw(_('No schedule'))

	return validations

def chk_holiday(employee, company, target_date):
	holiday_tag  = 0
	location = frappe.get_value("Employee", employee, "location")

	holiday = frappe.db.sql("""SELECT `name`, `company`, `location` FROM `tabHoliday` WHERE holiday_date = %s 
		AND company = %s """, (target_date, company), as_dict=True)

	if holiday:
		for hol in holiday:
			if hol.location:
				if location == hol.location:
					holiday_tag = 1
			else:
				holiday_tag = 1

	return holiday_tag

def use_validate_cto(**entry):
	credits_earned, last_earned_date = get_total_credits_earned(employee=entry['employee'], filed_cto=entry['filed_cto'], target_date=entry['target_date'])
	if last_earned_date:
		if getdate(entry['target_date']) < getdate(last_earned_date):
			frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Insufficient Balance").format(entry['application_name']))

	shifts = None
	schedule = get_schedule(entry['employee'], entry['target_date'], entry['target_date'])
	if schedule:
		shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0]['work_shift']), as_dict=True)

	if shifts:
		if entry['type'] == "Use":
			if int(shifts[0].cto_min_usage_hrs) > 0:
				if entry['total_hours'] < shifts[0].cto_min_usage_hrs:
					frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Minimum hours of usage is {1}").format(entry['application_name'], shifts[0].cto_min_usage_hrs))
			if int(shifts[0].cto_max_usage_hrs) > 0:
				if entry['total_hours'] > shifts[0].cto_max_usage_hrs:
					frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Maximum hours of usage is {1}").format(entry['application_name'], shifts[0].cto_max_usage_hrs))

	if flt(entry['required_credits'], 2) > flt(entry['credits_earned'], 2):
		frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> You dont have enough credits for date {1}").format(entry['application_name'], entry['target_date']))	

	if entry['required_credits'] <= 0:
		frappe.throw(_("<b>Compensatory Time Off: {0}</b><hr> Required Credits for date {1} must be greater than 0").format(entry['application_name'], entry['target_date']))

def validate_strict_cto(**entry):
	if frappe.db.get_single_value('Timekeeping Settings', 'cto_strict'):
		ot_app = frappe.db.sql("""SELECT `name` FROM `tabOvertime Application` WHERE `target_date` = %s AND `employee` = %s AND `workflow_state` = "Approved" 
			AND ((`to_time` BETWEEN  %s AND %s) OR (`from_time` BETWEEN  %s AND %s))""",(entry['target_date'], entry['employee'], entry['from_time'], entry['to_time'], entry['from_time'], entry['to_time']), as_dict=True)
		if ot_app:
			frappe.throw(_("There's already an Overtime Application filed with the same date."))

def get_table_summary(**entry):
	result = {}
	result['total_credits_earned'] = 0
	result['total_required_credits'] = 0
	result['total_credits_used'] = 0
	result['total_balance'] = 0
	result['total_break_hours'] = 0
	result['total_hours'] = 0

	for d in entry['rows']:
		if entry['type'] == 'File':
			result['total_credits_earned'] += flt(d['credits_earned'])
		else:
			result['total_credits_earned'] += flt(d['total_credits_earned'])
		result['total_required_credits'] += flt(d['required_credits'])
		result['total_credits_used'] += flt(d['credits_used'])
		result['total_balance'] += flt(d['balance'])
		result['total_break_hours'] += flt(d['break_hours'])
		result['total_hours'] += flt(d['cto_hours'])

	return result

def update_cto_table_summary(update_cto_table_list, _type):
	for cto_name in update_cto_table_list:
		cto = frappe.get_doc("Compensatory Time Off", cto_name)
		table_rows = []
		included_cto_credits = []
		total_credits_earned = 0
		for d in cto.cto_targets:
			total_credits_earned = 0
			if d.name not in included_cto_credits:
				total_credits_earned += d.credits_earned

			table_rows.append({
				'credits_earned': d.credits_earned,
				'required_credits': d.required_credits,
				'credits_used': d.credits_used,
				'balance': d.balance,
				'break_hours': d.break_hours,
				'cto_hours': d.cto_hours,
				'total_credits_earned': total_credits_earned,
			})
			
		table_summary = get_table_summary(rows=table_rows, type=_type)
		if table_summary['total_credits_earned'] < 0:
			table_summary['total_credits_earned'] = 0
		if table_summary['total_required_credits'] < 0:
			table_summary['total_required_credits'] = 0
		if table_summary['total_credits_used'] < 0:
			table_summary['total_credits_used'] = 0
		if table_summary['total_balance'] < 0:
			table_summary['total_balance'] = 0
		if table_summary['total_break_hours'] < 0:
			table_summary['total_break_hours'] = 0
		if table_summary['total_hours'] < 0:
			table_summary['total_hours'] = 0

		frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET 
			total_credits_earned = %s,
			total_required_credits = %s,
			total_credits_used = %s,
			total_balance = %s,
			total_break_hours = %s,
			total_hours = %s 
			WHERE `name` = %s AND docstatus = 1 """, (
			table_summary['total_credits_earned'],
			table_summary['total_required_credits'],
			table_summary['total_credits_used'],
			table_summary['total_balance'],
			table_summary['total_break_hours'],
			table_summary['total_hours'],
			cto_name
		))

def validate_filed_cto(**entry):
	cto_target = frappe.db.sql("""SELECT `target_date` FROM `tabCompensatory Time Off Targets` WHERE `parent`=%s AND `target_date` <= %s """,(entry['filed_cto'], entry['target_date']), as_dict=True)
	if not cto_target:
		frappe.throw(_( "Filed CTO for Date {0} is not within Target Date".format(entry['target_date']) ))

def prompt_validation_messages(validations):
	validation_result = {}

	for v in validations:
		if v['validation'] == 'No Actual Logs':
			if 'No Actual Logs' not in validation_result:
				validation_result['No Actual Logs'] = []
			validation_result['No Actual Logs'].append( str(getdate(v['target_date'])) )

		if v['validation'] == 'Incomplete Actual Logs':
			if 'Incomplete Actual Logs' not in validation_result:
				validation_result['Incomplete Actual Logs'] = []
			validation_result['Incomplete Actual Logs'].append( str(getdate(v['target_date'])) )

		if v['validation'] == 'File From is not within your actual logs':
			if 'File From is not within your actual logs' not in validation_result:
				validation_result['File From is not within your actual logs'] = []
			validation_result['File From is not within your actual logs'].append( str(getdate(v['target_date'])) )

		if v['validation'] == 'File To is not within your actual logs':
			if 'File To is not within your actual logs' not in validation_result:
				validation_result['File To is not within your actual logs'] = []
			validation_result['File To is not within your actual logs'].append( str(getdate(v['target_date'])) )

	if 'No Actual Logs' in validation_result:
		targets = "<br>".join( validation_result['No Actual Logs'] )
		frappe.throw(_( "You have no actual logs for the following Dates <br> {0}".format(targets) ))

	if 'Incomplete Actual Logs' in validation_result:
		targets = "<br>".join( validation_result['Incomplete Actual Logs'] )
		frappe.throw(_( "You have incomplete actual logs for the following Dates <br> {0}".format(targets) ))

	if 'File From is not within your actual logs' in validation_result:
		targets = "<br>".join( validation_result['File From is not within your actual logs'] )
		frappe.throw(_( "File From of the following Dates are not within your actual logs <br> {0}".format(targets) ))

	if 'File To is not within your actual logs' in validation_result:
		targets = "<br>".join( validation_result['File To is not within your actual logs'] )
		frappe.throw(_( "File To of the following Dates are not within your actual logs <br> {0}".format(targets) ))