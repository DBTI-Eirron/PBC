
from __future__ import unicode_literals
import frappe, datetime
from frappe import msgprint, _
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, comma_or, get_fullname, nowdate
from frappe.email import queue
from workwise.time_keeping.timekeeping_utils import datediff_days_raw
from workwise.payroll.policy_utils import get_policy
from workwise.time_keeping.application_utils import grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, change_owner, get_levelled_approval, get_levelled_approval_rejection
from frappe.model.document import Document

class LeaveApplication(Document):
	def validate(self):
		grant_head_subordinate_access(self)
		self.validate_schedule();
		self.set_lwop()
		self.validate_leave_table()
		self.validate_days()
		self.validate_date()
		self.validate_employee()
		self.validate_balance()
		self.validate_medical()
		self.validate_leave()
		change_owner(self)
		self.get_recipients()

	def on_submit(self):
		self.set_lwop()
		validate_approve_own_application(self)
		self.validate_medical()
		self.validate_balance()
		self.update_leave_credits()
		get_approver_and_date(self)

	def before_update_after_submit(self):
		get_levelled_approval(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		frappe.db.sql("""UPDATE `tabLeave Balance` SET used_credits = used_credits - %s 
			WHERE name = %s """, (self.total_leave_days, self.from_balance))

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

	def validate_schedule(self):
		result = frappe.db.sql("""SELECT SUM(WSS.is_restday) AS restday FROM `tabWork Schedule` WS INNER JOIN `tabWork Shift` WSS ON WS.work_shift = WSS.`name` WHERE WS.employee = %s AND WS.target_date BETWEEN %s and %s""",(self.employee,self.from_date,self.to_date),as_dict=True)
		if result[0].restday > 0:
			frappe.throw("Can't file leave on Restday Schedule")
	def update_leave_credits(self):
		frappe.db.sql("""UPDATE `tabLeave Balance` SET used_credits = used_credits + %s 
			WHERE name = %s """, (self.total_leave_days, self.from_balance))

	def validate_leave(self):
		max_days, filing_days = frappe.get_value("Leave Type", self.leave_type, ["max_days", "filing_days"])
		if max_days > 0:
			if self.total_leave_days > max_days:
				frappe.throw(_("<b>Leave Application: {0}</b><hr> Maximum of {2} Day(s) are Allowed for ( {1} )").format(self.name, self.leave_type, max_days))

		if filing_days > 0:
			date_diff=datediff_days_raw(nowdate(), cstr(self.from_date), "%Y-%m-%d")		
			if date_diff.days > filing_days:
				frappe.throw(_("<b>Leave Application: {0}</b><hr> Date of Filling should not be later than {1} Day(s)").format(self.name, filing_days))

	def set_lwop(self):
		is_lwop = frappe.get_value("Leave Type", self.leave_type, "is_lwop")
		if is_lwop:
			self.is_lwop = 1
		else:
			self.is_lwop = 0

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
					emp_bday = datetime.datetime.strptime(str(emp_bday), '%Y-%m-%d')
					from_date = datetime.datetime.strptime(self.from_date, '%Y-%m-%d')
					if emp_bday.strftime('%m-%d') != from_date.strftime('%m-%d'):
						frappe.throw(_("<b>Leave Application: {0}</b><hr> You can only file Birthday Leave on your birthday").format(self.name))

	def validate_days(self):
		self.total_leave_days = self.get_total_leave_days()
		self.leave_balance = self.get_leave_balance()

	def chk_holiday(self, target_date):
		holiday_tag  = 0
		location = frappe.get_value("Employee", self.employee, "location")

		holiday = frappe.db.sql("""SELECT `name` FROM `tabHoliday` WHERE holiday_date = %s 
			AND company = %s AND location = %s """, (target_date, self.company, location), as_dict=True)

		if holiday:
			holiday_tag = 1

		return holiday_tag 
	
	def get_total_leave_days(self):
		total_leave_days = 0
		inc_holidays = frappe.get_value("Leave Type", self.leave_type, "include_holidays")

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
				lvbal_saturday = frappe.db.get_single_value('Timekeeping Settings', 'lvbal_saturday')
				if lvbal_saturday > 0:
					add_days = flt(lvbal_saturday, 8)

			if d.is_excluded == 1:
				add_days = 0
				
			total_leave_days += add_days

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
			total_balance = flt(self.leave_balance, 2) - flt(self.total_leave_days, 2)
			if total_balance < 0 and not self.is_lwop:
				frappe.throw(_("<b>Leave Application: {0}</b><hr> Not enough Leave Credits {1}").format(self.name, self.total_leave_days))
			
			if not self.from_balance:
				frappe.throw(_("<b>Leave Application: {0}</b><hr> Leave Balance is Required").format(self.name))

	def validate_date(self):
		if self.from_date > self.to_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> From Date must be before To Date").format(self.name))

		for d in self.get('leave_application_table'):
			if d.is_excluded < 1:
				wholeday_exist = frappe.db.sql(""" SELECT DISTINCT LA.`name` FROM `tabLeave Application Table` LT INNER JOIN `tabLeave Application` LA ON LT.`parent`=LA.`name` WHERE LA.docstatus = 1 AND LA.`employee` = %s AND LT.`leave_date` = %s AND LT.is_second_half = 0 AND LT.is_half_day = 0 AND LA.`name` != %s """,(self.employee, d.leave_date, self.name), as_dict=True)
				if wholeday_exist:
					frappe.throw(_("<b>Leave Application: {0}</b><hr> {1} already has a filed leave on {2}. Leave Application: {3}").format(self.name, self.full_name, d.leave_date, wholeday_exist[0].name))
				if d.is_half_day < 1 and d.is_second_half < 1:
					half_exist = frappe.db.sql(""" SELECT DISTINCT LA.`name` FROM `tabLeave Application Table` LT INNER JOIN `tabLeave Application` LA ON LT.`parent`=LA.`name` WHERE LA.docstatus = 1 AND LA.`employee` = %s AND LT.`leave_date` = %s AND LT.is_half_day = 1 AND LA.`name` != %s """,(self.employee, d.leave_date, self.name), as_dict=True)
					if half_exist:
						frappe.throw(_("<b>Leave Application: {0}</b><hr> {1} already has a filed leave on {2}. Leave Application: {3}").format(self.name, self.full_name, d.leave_date, half_exist[0].name))
				if d.is_half_day > 0 and d.is_second_half < 1:
					if wholeday_exist:
						frappe.throw(_("<b>Leave Application: {0}</b><hr> {1} already has a filed leave on {2}. Leave Application: {3}").format(self.name, self.full_name, d.leave_date, wholeday_exist[0].name))
					firsthalf_exist = frappe.db.sql(""" SELECT DISTINCT LA.`name` FROM `tabLeave Application Table` LT INNER JOIN `tabLeave Application` LA ON LT.`parent`=LA.`name` WHERE LA.docstatus = 1 AND LA.`employee` = %s AND LT.`leave_date` = %s AND LT.is_half_day = 1 AND LT.is_second_half = 0 AND LA.`name` != %s """,(self.employee, d.leave_date, self.name), as_dict=True)
					if firsthalf_exist:
						frappe.throw(_("<b>Leave Application: {0}</b><hr> {1} already has a filed leave on {2}. Leave Application: {3}").format(self.name, self.full_name, d.leave_date, firsthalf_exist[0].name))
				if d.is_second_half > 0:
					if wholeday_exist:
						frappe.throw(_("<b>Leave Application: {0}</b><hr> {1} already has a filed leave on {2}. Leave Application: {3}").format(self.name, self.full_name, d.leave_date, wholeday_exist[0].name))
					secondhalf_exist = frappe.db.sql(""" SELECT DISTINCT LA.`name` FROM `tabLeave Application Table` LT INNER JOIN `tabLeave Application` LA ON LT.`parent`=LA.`name` WHERE LA.docstatus = 1 AND LA.`employee` = %s AND LT.`leave_date` = %s AND LT.is_second_half = 1 AND LA.`name` != %s """,(self.employee, d.leave_date, self.name), as_dict=True)
					if secondhalf_exist:
						frappe.throw(_("<b>Leave Application: {0}</b><hr> {1} already has a filed leave on {2}. Leave Application: {3}").format(self.name, self.full_name, d.leave_date, secondhalf_exist[0].name))

	def validate_medical(self):
		if self.leave_type == "Sick Leave":
			#valid_day = frappe.db.get_single_value('Timekeeping Settings', 'require_medical')
			valid_day = get_policy("TK-REQMED" ,self.company)
			if valid_day:
				if flt(self.total_leave_days, 2) >= flt(valid_day, 2) and not self.medical_cert:
					frappe.throw(_("<b>Leave Application: {0}</b><hr> Medical Certificate Required").format(self.name))
				
	def get_leaves_balances(self):
		total_balance = 0
		self.set('leave_application_table', [])
		if not self.from_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> No From Date").format(self.name))

		if not self.to_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> No To Date").format(self.name))
		
		if self.from_date > self.to_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> To From Date Should be Greater than To").format(self.name))
			
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
			
			total_balance = self.get_leave_balance()

		self.leave_balance = self.get_leave_balance()
		self.total_leave_days = self.get_total_leave_days()

	def get_leave_balance(self):
		self.from_balance = ""
		total_balance = 0
		deduct_balance = ""

		deduct = frappe.db.sql(""" SELECT `name`, `deduct_to` FROM `tabLeave Type` LT WHERE `name` = %s LIMIT 1 """, (self.leave_type), as_dict=True)

		if deduct:
			if deduct[0].deduct_to:
				deduct_balance = deduct[0].deduct_to
			else:
				deduct_balance = deduct[0].name

		bal = frappe.db.sql("""SELECT `name`, credits, used_credits, from_date, to_date FROM `tabLeave Balance` WHERE employee = %s 
			AND leave_type = %s AND (%s BETWEEN from_date AND to_date) AND (%s BETWEEN from_date AND to_date) """, (self.employee, deduct_balance, self.from_date, self.to_date), as_dict=True)

		if bal:
			total_balance = flt(bal[0]['credits'], 2) - flt( bal[0]['used_credits'], 2)
			self.from_balance = bal[0]['name']

		return total_balance

@frappe.whitelist()
def get_number_of_leave_days(from_date, to_date, half_day=None):
	if half_day==1:
		return 0.5
	number_of_days = date_diff(to_date, from_date) + 1

	return number_of_days
