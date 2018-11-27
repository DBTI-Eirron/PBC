
from __future__ import unicode_literals
import frappe, datetime
from frappe import msgprint, _
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, comma_or, get_fullname, nowdate
from frappe.email import queue
from workwise.time_keeping.timekeeping_utils import datediff_days_raw
from workwise.payroll.policy_utils import get_policy
from workwise.time_keeping.application_utils import grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, change_owner
from frappe.model.document import Document

class LeaveApplication(Document):
	def validate(self):
		grant_head_subordinate_access(self)
		self.set_lwop()
		self.validate_leave_table()
		self.validate_days()
		self.validate_date()
		self.validate_employee()
		self.validate_balance()
		self.validate_medical()
		change_owner(self)
		self.get_recipients()

	def on_submit(self):
		self.set_lwop()
		validate_approve_own_application(self)
		self.validate_medical()
		self.validate_leave()
		self.validate_balance()
		self.update_leave_credits()
		get_approver_and_date(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
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

	def update_leave_credits(self):
		frappe.db.sql("""UPDATE `tabLeave Balance` SET used_credits = used_credits + %s 
			WHERE name = %s """, (self.total_leave_days, self.from_balance))

	def validate_leave(self):
		max_days, filing_days = frappe.get_value("Leave Type", self.leave_type, ["max_days", "filing_days"])
		if max_days > 0:
			if self.total_leave_days > max_days:
				frappe.throw(_("Maximum of {1} Day(s) are Allowed for ( {0} ) ").format(self.leave_type, max_days))

		if filing_days > 0:
			date_diff=datediff_days_raw(nowdate(), cstr(self.from_date), "%Y-%m-%d")		
			if date_diff.days > filing_days:
				frappe.throw(_("Date of Filling should not be later than {0} Day(s) ").format(filing_days))

	def set_lwop(self):
		is_lwop = frappe.get_value("Leave Type", self.leave_type, "is_lwop")
		if is_lwop:
			self.is_lwop = 1
		else:
			self.is_lwop = 0

	def validate_employee(self):
		access_list = []
		solo, gender, civil_status, employment_status = frappe.get_value("Employee", self.employee, ["is_solo_parent", "gender", "civil_status", "employment_status"])
		f_only, m_only, mr_only, sp_only = frappe.get_value("Leave Type", self.leave_type, ["female_only", "male_only", "married_only", "solo_parent_only"])

		if f_only == 1 and gender != 'Female':
			frappe.throw(_("Leave Type is for Female Only"))

		if m_only == 1 and gender != 'Male':
			frappe.throw(_("Leave Type is for Male Only"))

		if mr_only == 1 and civil_status != 'Married':
			frappe.throw(_("Leave Type is for Married Only"))

		if sp_only == 1 and solo != 1:			
			frappe.throw(_("Leave Type is for Solo Only"))

		allow_from_employment_status = frappe.db.sql(""" SELECT DISTINCT employment_status FROM `tabLeave Type Table` WHERE `parent` = %s """, (self.leave_type), as_dict=True)

		if allow_from_employment_status:
			for a in allow_from_employment_status:
				access_list.append(a.employment_status)

			if employment_status not in access_list:
				frappe.throw(_("Employement Status {0} is not allowed for {1}").format(employment_status ,self.leave_type))

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
			frappe.throw(_("No From Date"))

		if not self.to_date:
			frappe.throw(_("No To Date"))
		
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
				frappe.throw(_("Not enough Leave Credits {0}").format(self.total_leave_days))
			
			if not self.from_balance:
				frappe.throw(_("Leave Balance is Required"))

	def validate_date(self):
		if self.from_date > self.to_date:
			frappe.throw(_("From Date must be before To Date"))

		for d in self.get('leave_application_table'):
			exist = frappe.db.sql("""SELECT LAP.`name` FROM `tabLeave Application` LA 
				INNER JOIN `tabLeave Application Table` LAP ON LAP.parent = LA.`name`
				WHERE LAP.leave_date = %s AND LA.employee = %s  AND LA.leave_type = %s AND LA.docstatus = 1 """,(d.leave_date, self.employee, self.leave_type) )
			if exist:
				frappe.throw(_("{0} already has a {1} Filed on {2}").format(self.full_name, self.leave_type, d.leave_date))

	def validate_medical(self):
		if self.leave_type == "Sick Leave":
			#valid_day = frappe.db.get_single_value('Timekeeping Settings', 'require_medical')
			valid_day = get_policy("TK-REQMED" ,self.company)
			if valid_day:
				if flt(self.total_leave_days, 2) >= flt(valid_day, 2) and not self.medical_cert:
					frappe.throw(_("Medical Certificate Required"))
				
	def get_leaves_balances(self):
		total_balance = 0
		self.set('leave_application_table', [])
		if not self.from_date:
			frappe.throw(_("No From Date"))

		if not self.to_date:
			frappe.throw(_("No To Date"))
		
		if self.from_date > self.to_date:
			frappe.throw(_("To From Date Should be Greater than To"))
			
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
