
from __future__ import unicode_literals
import frappe, datetime
from frappe import msgprint, _
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, comma_or, get_fullname, nowdate
from frappe.email import queue
from workwise.time_keeping.timekeeping_utils import datediff_days_raw
from workwise.payroll.policy_utils import get_policy
from workwise.time_keeping.attendance_utils import get_schedule
from workwise.time_keeping.application_utils import ( grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, get_employee_details,
change_owner, get_levelled_approval, get_levelled_approval_rejection, clear_approval_history, validate_inactive_employee, get_approver_email_list, get_cancelled_by_and_date, validate_approver_userperm, validate_cutoff_approval_date)
from frappe.model.document import Document

class LeaveApplication(Document):
	def validate(self):
		get_employee_details(self)
		validate_inactive_employee(self)
		clear_approval_history(self)
		grant_head_subordinate_access(self)
		self.clear_fields()
		self.validate_schedule()
		self.set_lwop()
		self.validate_leave_table()
		self.validate_days()
		self.validate_employee()
		if self.docstatus not in [1, '1', 2, '2']:
			self.validate_leave()
		self.validate_convertible()
		change_owner(self)
		self.get_recipients()
		if self.workflow_state == "Pending" or self.workflow_state == "Draft":
			self.validate_date()
			self.validate_filing_in_holiday()
			self.validate_balance()

	def on_submit(self):
		self.validate_date()
		self.set_lwop()
		self.validate_filing_in_holiday()
		validate_approve_own_application(self)
		self.validate_medical()
		self.validate_balance()
		self.update_leave_credits()
		get_approver_and_date(self)
		get_approver_email_list(self, 'on_submit')
		#validate_approver_userperm(self)
		validate_cutoff_approval_date(self)

	def on_update(self):
		validate_reject_cancel_own_application(self)

	def before_update_after_submit(self):
		self.validate_balance()
		self.validate_date()
		self.validate_days()
		self.validate_balance()
		self.validate_filing_in_holiday()
		get_approver_email_list(self, 'before_update_after_submit')
		get_levelled_approval(self)
		#validate_approver_userperm(self)
		validate_cutoff_approval_date(self)
		self.update_leave_credits()

	def on_cancel(self):
		self.validate_without_lbentry()
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		get_cancelled_by_and_date(self)
		self.revert_leave_credits()

	def validate_filing_in_holiday(self):
		inc_holidays, allow_holiday_filing, leave_code = frappe.get_value("Leave Type", self.leave_type, ["include_holidays", "allow_holiday_filing","leave_code"])
		for d in self.get('leave_application_table'):
			if d.is_holiday == 1 and d.is_excluded == 0:
				if inc_holidays == 1:
					if allow_holiday_filing != 1:
						frappe.throw(_("<b>Leave Application: {0}</b><hr> Can't File on Holiday").format(self.name))
				else:
					frappe.throw(_("<b>Leave Application: {0}</b><hr> Can't File on Holiday ").format(self.name))

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

	def clear_fields(self):
		self.linked_lb_entry = None

	def validate_schedule(self):
		leave_code, allow_rest_day = frappe.get_value("Leave Type", self.leave_type, ["leave_code", "allow_rest_day"])
		for d in self.get('leave_application_table'):
			if not d.is_excluded:
				schedule = get_schedule(self.employee, d.leave_date, d.leave_date)
				if schedule:
					shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0]['work_shift']), as_dict=True)
					if shifts:
						if shifts[0].is_restday > 0:
							if (not leave_code == 'BL') and (allow_rest_day != 1):
								frappe.throw("Can't file leave on Restday Schedule")

	def validate_leave(self):
		max_days, is_allow_beyond = frappe.get_value("Leave Type", self.leave_type, ["max_days", "is_allow_beyond"])
		if max_days > 0:
			if not is_allow_beyond:
				if self.total_leave_days > max_days:
					frappe.throw(_("<b>Leave Application: {0}</b><hr> Maximum of {2} Day(s) are Allowed for ( {1} )").format(self.name, self.leave_type, max_days))

		#Days Before Filing
		dbf = frappe.db.sql(""" SELECT * FROM `tabLeave Type Before Filing Table` WHERE `parent` = %s """,(self.leave_type), as_dict=1)
		if dbf:
			lv_count = frappe.db.sql(""" SELECT COUNT(*) as count FROM `tabLeave Application` WHERE workflow_state = 'Approved' AND docstatus = 1
				AND `company` = %s AND `employee` = %s AND `leave_type` = %s """,(self.company, self.employee, self.leave_type), as_dict=1)

			count_lv = lv_count[0].count+self.total_leave_days
			if frappe.db.get_single_value('Timekeeping Settings', 'lv_before_filing_per_app'):
				count_lv = self.total_leave_days

			for df in dbf:
				trigger_validation = 0
				if not df.from_leave_day or not df.to_leave_day:
					trigger_validation = 1
					
				if df.from_leave_day and df.to_leave_day and df.from_leave_day <= count_lv <= df.to_leave_day:
					trigger_validation = 1

				if trigger_validation:
					only_from_date = datetime.datetime.strptime(str(self.from_date), '%Y-%m-%d') - datetime.timedelta(days=df.days_before_filing)
					only_to_date = datetime.datetime.strptime(str(self.to_date), '%Y-%m-%d') - datetime.timedelta(days=df.days_before_filing)
					date_list = [only_from_date, only_to_date]
					for dt in date_list:
						if getdate(nowdate()) > getdate(dt):
							frappe.throw(_("<b>Leave Application: {0}</b><hr> You can only file {1} day(s) before {2} ").format(self.name, df.days_before_filing, self.from_date ))
							break

	def set_lwop(self):
		is_lwop = frappe.get_value("Leave Type", self.leave_type, "is_lwop")
		if is_lwop:
			self.is_lwop = 1
		else:
			self.is_lwop = 0

	def validate_convertible(self):
		convertible = frappe.get_value("Leave Type", self.leave_type, "convertible")
		if self.convert_cash and (not convertible):
			frappe.throw(_("{0} is not Convertible to Cash").format(self.leave_type))

	def validate_employee(self):
		access_list = []
		solo, gender, civil_status, employment_status = frappe.get_value("Employee", self.employee, ["is_solo_parent", "gender", "civil_status", "employment_status"])
		f_only, m_only, mr_only, sp_only, allow_advance_filing, leave_code, filed_on_bday = frappe.get_value("Leave Type", self.leave_type, ["female_only", "male_only", "married_only", "solo_parent_only", "allow_advance_filing", "leave_code", "filed_on_bday"])

		if f_only == 1 and gender != 'Female':
			frappe.throw(_("<b>Leave Application: {0}</b><hr> Leave Type is for Female Only").format(self.name))

		if m_only == 1 and gender != 'Male':
			frappe.throw(_("<b>Leave Application: {0}</b><hr> Leave Type is for Male Only").format(self.name))

		if mr_only == 1 and civil_status != 'Married':
			frappe.throw(_("<b>Leave Application: {0}</b><hr> Leave Type is for Married Only").format(self.name))

		if sp_only == 1 and solo != 1:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> Leave Type is for Solo Only").format(self.name))

		allow_from_employment_status = frappe.db.sql(""" SELECT DISTINCT employment_status FROM `tabLeave Type Table` WHERE `parent` = %s """, (self.leave_type), as_dict=True)

		if allow_from_employment_status:
			for a in allow_from_employment_status:
				access_list.append(a.employment_status)

			if employment_status not in access_list:
				frappe.throw(_("<b>Leave Application: {0}</b><hr> Employement Status {1} is not allowed for {2}").format(self.name, employment_status, self.leave_type))

		if allow_advance_filing == 0:
			if self.from_date > nowdate() or self.to_date > nowdate():
				frappe.throw(_("<b>Leave Application: {0}</b><hr> You cannot file in advance for {1}").format(self.name, self.leave_type))

		if leave_code == "BL":
			if filed_on_bday == 1:
				emp_bday = frappe.db.get_value("Employee", self.employee, "birthday")
				if emp_bday:
					for d in self.get('leave_application_table'):
						emp_bday = datetime.datetime.strptime(str(emp_bday), '%Y-%m-%d')
						from_date = datetime.datetime.strptime(d.leave_date, '%Y-%m-%d')
						if emp_bday.strftime('%m-%d') != from_date.strftime('%m-%d'):
							frappe.throw(_("<b>Leave Application: {0}</b><hr> You can only file Birthday Leave on your birthday").format(self.name))

	def validate_days(self):
		self.total_leave_days = self.get_total_leave_days()
		self.get_leave_balance()

	def chk_holiday(self, target_date):
		holiday_tag  = 0
		location = frappe.get_value("Employee", self.employee, "location")

		holiday = frappe.db.sql("""SELECT `name`, location FROM `tabHoliday` WHERE holiday_date = %s 
			AND company = %s """, (getdate(target_date), self.company), as_dict=True)

		if holiday:
			if holiday[0].location:
				if holiday[0].location == location:
					holiday_tag = 1	
			else:
				holiday_tag = 1

		return holiday_tag 
	
	def get_total_leave_days(self):
		total_leave_days = 0
		inc_holidays, leave_code = frappe.get_value("Leave Type", self.leave_type, ["include_holidays", "leave_code"])

		for d in self.get('leave_application_table'):
			add_days = 1

			if d.is_half_day == 1:
				add_days = 0.5			
			
			if d.is_holiday == 1:
				if inc_holidays == 1:
					add_days = 1
				else:
					add_days = 0
			
			if d.is_second_half == 1:
				d.is_half_day = 1
				add_days = 0.5

			if getdate(d.leave_date).weekday() == 5:
				lvbal_saturday = frappe.get_value("Employee", self.employee, "lvbal_saturday")
				if lvbal_saturday > 0:
					add_days = flt(lvbal_saturday, 8)

			if d.is_excluded == 1:
				add_days = 0
				
			total_leave_days += add_days

			if leave_code == "BL":
				schedule = get_schedule(self.employee, d.leave_date, d.leave_date)
				if schedule:
					shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0]['work_shift']), as_dict=True)
					if shifts:
						if shifts[0].is_restday > 0:
							total_leave_days = 0
				holiday_leave = self.chk_holiday(d.leave_date)
				if holiday_leave:
					total_leave_days = 0

		return total_leave_days

	def validate_leave_table(self):
		if not self.from_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> No From Date").format(self.name))

		if not self.to_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> No To Date").format(self.name))
		
		entries = [];
		dates = [];

		start = datetime.datetime.strptime(str(self.from_date), '%Y-%m-%d')
		end = datetime.datetime.strptime(str(self.to_date), '%Y-%m-%d')
		step = datetime.timedelta(days=1)

		while start <= end:
			dates.append(cstr(start.strftime('%Y-%m-%d')));
			start += step

		for d in self.get('leave_application_table'):
			entries.append(d.leave_date)

		#for d in dates:
		#	if getdate(d) not in entries:
		#		frappe.throw(_("Missing Data For {0}, For Leave {1}").format(d, self.name))

		#for en in entries:
		#	if getdate(en) not in dates:
		#		frappe.throw(_("{0} is not within {1} to {2}").format(en, self.from_date, self.to_date))

	def validate_balance(self):
		allow_negative = frappe.get_value("Leave Type", self.leave_type, "is_allow_negative")
		if allow_negative < 1:
			#if not self.from_balance:
			#	frappe.throw(_("<b>Leave Application: {0}</b><hr> Leave Balance is Required").format(self.name))

			total_balance = flt(self.leave_balance, 2) - flt(self.total_leave_days, 2)
			if total_balance < 0 and not self.is_lwop:
				frappe.throw(_("<b>Leave Application: {0}</b><hr> Not enough Leave Credits {1}").format(self.name, self.total_leave_days))

			#cur_credits = frappe.get_value("Leave Balance", self.from_balance, "credits")
			#if cur_credits < self.total_leave_days and not self.is_lwop:
			#	frappe.throw(_("<b>Leave Application: {0}</b><hr> Not enough Leave Credits {1}").format(self.name, self.total_leave_days))

	def validate_date(self):
		if self.from_date > self.to_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> From Date must be before To Date").format(self.name))

		for d in self.get('leave_application_table'):
			if d.is_excluded < 1:
				wholeday_exist = self.get_filed_leave_schedule(d.leave_date, 'wholeday', 0, 0)
				if d.is_half_day < 1 and d.is_second_half < 1:
					half_exist = self.get_filed_leave_schedule(d.leave_date, 'half day', 1, 0)
				if d.is_half_day > 0 and d.is_second_half < 1:
					wholeday_exist = self.get_filed_leave_schedule(d.leave_date, 'wholeday', 0, 0)
					firsthalf_exist = self.get_filed_leave_schedule(d.leave_date, 'first half', 1, 0)
				if d.is_second_half > 0:
					wholeday_exist = self.get_filed_leave_schedule(d.leave_date, 'wholeday', 0, 0)
					secondhalf_exist = self.get_filed_leave_schedule(d.leave_date, 'second half', 0, 1)

	def get_filed_leave_schedule(self, leave_date, sched_req, is_half_day, is_second_half):
		conditions = ""
		if sched_req == 'wholeday' or sched_req == 'first half':
			conditions = " AND LT.is_second_half=%(is_second_half)s AND LT.is_half_day=%(is_half_day)s"
		if sched_req == 'half day':
			conditions = " AND LT.is_half_day=%(is_half_day)s"
		if sched_req == 'second half':
			conditions = " AND LT.is_second_half=%(is_second_half)s"

		leave_sched = frappe.db.sql(""" SELECT DISTINCT LA.`name` FROM `tabLeave Application Table` LT INNER JOIN `tabLeave Application` LA ON LT.`parent`=LA.`name` 
		  	WHERE LA.workflow_state = "Approved" AND LA.`employee` = %(employee)s AND LT.`leave_date` = %(leave_date)s AND LT.`is_excluded` = 0 AND LA.`name` != %(leave_app)s {conditions}""".format(conditions=conditions),
			({ 
				"employee": self.employee,
				"leave_date": leave_date,
				"leave_app": self.name,
				"is_second_half": is_second_half,
				"is_half_day": is_half_day,
			}), as_dict=True)

		if leave_sched:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> {1} already has a filed {4} leave on {2}. Leave Application: {3}").format(self.name, self.full_name, leave_date, leave_sched[0].name, sched_req))

	def validate_medical(self):
		if self.leave_type == "Sick Leave":
			valid_day = frappe.db.get_single_value('Timekeeping Settings', 'require_medical')
			#valid_day = get_policy("TK-REQMED" ,self.company)
			if valid_day:
				if (flt(self.total_leave_days, 2) >= flt(valid_day, 2)) and not self.medical_cert:
					frappe.throw(_("<b>Leave Application: {0}</b><hr> Medical Certificate Required").format(self.name))
				
	def get_leaves_balances(self):
		total_balance = 0
		self.set('leave_application_table', [])
		if not self.from_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> No From Date").format(self.name))

		if not self.to_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> No To Date").format(self.name))
		
		if self.from_date > self.to_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> From Date must be before To Date").format(self.name))
			
		else:
			entries = [];
			dates = [];
			leave_application_table = [];

			start = datetime.datetime.strptime(self.from_date, '%Y-%m-%d')
			end = datetime.datetime.strptime(self.to_date, '%Y-%m-%d')
			step = datetime.timedelta(days=1)
			
			while start <= end:
			    dates.append(start.date());
			    start += step
			    
			for i in dates:
			    info = {
			        "leave_date": i,
			        "is_holiday": self.chk_holiday(i),
			        "is_halfday": 0,
			        "is_excluded": 0
			    }
			    
			    leave_application_table.append(info);
			
			entries = sorted(list(leave_application_table), 
				key=lambda k: k['leave_date'])		    

			self.set('leave_application_table', [])
			
			for d in entries:
				row = self.append('leave_application_table', {})
				row.update(d)
			
			self.get_leave_balance()
		self.total_leave_days = self.get_total_leave_days()
		self.get_leave_balance()

	def get_leave_balance(self):
		valid_entry = {}
		less_entry = {}
		from_balance = ""
		add, less, total_balance = 0, 0, 0
		min_date = None
		deduct_to = frappe.get_value("Leave Type", self.leave_type, "deduct_to")
		if not deduct_to:
			deduct_to = self.leave_type
		lb_entries = frappe.db.sql(""" SELECT * FROM `tabLB Entry` WHERE `employee` = %s AND 
			(`leave_type` = %s OR `deduct_credits_to` = %s) AND `company` = %s ORDER BY `from_date` 
			ASC """, (self.employee, deduct_to, deduct_to, self.company), as_dict=1)

		for d in lb_entries:
			if d.balance_type == "Add":
				if deduct_to == d.leave_type:
					if d.name not in valid_entry:
						valid_entry[d.name] = {
							"credits": d.credits,
							"from": getdate(d.from_date),
							"to": getdate(d.to_date),
							"used": 0,
						}
			else:
				if d.deduct_credits_to == deduct_to:
					if d.name not in less_entry:
						less_entry[d.name] = {
							"used": 0,
							"credits": d.credits,
							"from": getdate(d.from_date),
							"to": getdate(d.to_date),
						}

		have_lbentry = 0
		for vl in valid_entry:
			for le in less_entry:
				to_less = 0
				if valid_entry[vl]['credits'] > 0 and not less_entry[le]['used']:
					if ( valid_entry[vl]['from'] <= less_entry[le]['from'] <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= less_entry[le]['to'] <= valid_entry[vl]['to'] ):
						if less_entry[le]['credits'] > valid_entry[vl]['credits']:
							to_less += valid_entry[vl]['credits']
							less_entry[le]['credits'] -= valid_entry[vl]['credits']
						else:
							to_less += less_entry[le]['credits']
							less_entry[le]['used'] = 1
					valid_entry[vl]['credits'] -= to_less
			if getdate(valid_entry[vl]['from']) <= getdate(self.from_date) and getdate(valid_entry[vl]['to']) >= getdate(self.to_date) and valid_entry[vl]['credits'] > 0:
				if total_balance < self.total_leave_days:
					from_balance += cstr(vl)
				total_balance += valid_entry[vl]['credits']
				valid_entry[vl]['used'] = 1
				have_lbentry = 1
				
		if have_lbentry == 1:
			for vl in valid_entry:
				if valid_entry[vl]['used'] == 0 and valid_entry[vl]['credits'] > 0:
					if ( valid_entry[vl]['from'] <= getdate(self.from_date) <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= getdate(self.to_date) <= valid_entry[vl]['to'] )\
					or ( getdate(self.from_date) <= valid_entry[vl]['from'] <= getdate(self.to_date) ) or ( getdate(self.from_date) <= valid_entry[vl]['to'] <= getdate(self.to_date) ):
						if total_balance < self.total_leave_days:
							from_balance += cstr(vl)
						total_balance += valid_entry[vl]['credits']
						valid_entry[vl]['used'] = 1

		self.from_balance = from_balance
		if total_balance <= 0:
			total_balance = 0
		self.leave_balance = total_balance

	def update_leave_credits(self):
		if self.workflow_state == 'Approved' and not self.linked_lb_entry:
			deduct_to = frappe.get_value("Leave Type", self.leave_type, "deduct_to")
			if not deduct_to:
				deduct_to = self.leave_type

			lb = frappe.new_doc("LB Entry")
			lb.update({
				"employee": self.employee,
				"employee_name": self.full_name,
				"posting_date": nowdate(),
				"company": self.company,
				"leave_type": self.leave_type,
				"balance_type": 'Less',
				"created_from": 'Leave Application',
				"linked_document": self.name,
				"from_date": self.from_date,
				"to_date": self.to_date,
				"credits": self.total_leave_days,
				"deduct_credits_to": deduct_to,
			})
			lb.flags.ignore_permissions = True
			lb.insert()
			self.db_set("linked_lb_entry", lb.name)

	def revert_leave_credits(self):
		if self.linked_lb_entry:
			frappe.delete_doc('LB Entry', self.linked_lb_entry, ignore_permissions=True)
			self.db_set("linked_lb_entry", None)

	def validate_without_lbentry(self):
		if self.without_lbentry:
			frappe.throw(_('You cant cancel Leave Application without LB Entry'))


@frappe.whitelist()
def get_number_of_leave_days(from_date, to_date, half_day=None):
	if half_day==1:
		return 0.5
	number_of_days = date_diff(to_date, from_date) + 1

	return number_of_days
