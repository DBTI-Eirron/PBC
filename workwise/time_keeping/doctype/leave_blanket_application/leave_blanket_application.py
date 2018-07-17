# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import msgprint, _
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, comma_or, get_fullname, nowdate
from workwise.time_keeping.timekeeping_utils import datediff_days_raw
from frappe.model.document import Document

class LeaveBlanketApplication(Document):
	def validate(self):
		self.validate_leave_table()
		self.validate_days()
		self.validate_date()
		self.validate_employee()

	def on_submit(self):
		self.validate_leave()
		self.validate_balance()
		self.update_leave_credits()

	def on_cancel(self):
		frappe.db.sql("""UPDATE `tabLeave Balance` SET used_credits = used_credits - %s 
			WHERE name = %s """, (self.total_leave_days, self.from_balance))

	def validate_approval(self):
		if self.approval_status != "Open":
			approvers = frappe.db.sql("""SELECT * FROM `tabEmployee Leave Approver`
				WHERE parent = %s AND leave_approver = %s """, (self.employee, frappe.session.user), as_dict=True)
			if not approvers:
				frappe.throw(_("Not Allowed to Change Status"))

	def update_leave_credits(self):
		frappe.db.sql("""UPDATE `tabLeave Balance` SET used_credits = used_credits + %s 
			WHERE name = %s """, (self.total_leave_days, self.from_balance))

	def validate_leave(self):
		max_days, filing_days = frappe.get_value("Leave Type", self.leave_type, ["max_days", "filing_days"])
		if max_days > 0:
			if self.total_leave_days > max_days:
				frappe.throw(_("Maximum of {1} Day(s) are Allowed for ( {0} ) ").format(self.leave_type, max_days))

		if self.leave_type == "Sick Leave":
			if not medical_cert:
				frappe.throw(_("Medical Certificate is Required for Sick Leave"))

		if filing_days > 0:
			date_diff=datediff_days_raw(nowdate(), self.from_date, "%Y-%m-%d")		
			if date_diff.days > filing_days:
				frappe.throw(_("Date of Filling should not be later than {0} Day(s) ").format(filing_days))

	def validate_employee(self):
		solo, gender, civil_status = frappe.get_value("Employee", self.employee, ["is_solo_parent", "gender", "civil_status" ])
		f_only, m_only, mr_only, sp_only = frappe.get_value("Leave Type", self.leave_type, ["female_only", "male_only", "married_only", "solo_parent_only"])

		if f_only == 1 and gender != 'Female':
			frappe.throw(_("Leave Type is for Female Only"))

		if m_only == 1 and gender != 'Male':
			frappe.throw(_("Leave Type is for Male Only"))

		if mr_only == 1 and civil_status != 'Married':
			frappe.throw(_("Leave Type is for Married Only"))

		if sp_only == 1 and solo != 1:			
			frappe.throw(_("Leave Type is for Solo Only"))

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

		start = datetime.datetime.strptime(self.from_date, '%Y-%m-%d')
		end = datetime.datetime.strptime(self.to_date, '%Y-%m-%d')
		step = datetime.timedelta(days=1)

		while start <= end:
			dates.append(cstr(start.strftime('%Y-%m-%d')));
			start += step

		for d in self.get('leave_application_table'):
			entries.append(d.leave_date)

		for d in dates:
			if d not in entries:
				frappe.throw(_("Missing Data For {0}").format(d))

		for en in entries:
			if en not in dates:
				frappe.throw(_("{0} is not within {1} to {2}").format(en, self.from_date, self.to_date))

	def validate_balance(self):
		total_balance = flt(self.leave_balance, 2) - flt(self.total_leave_days, 2)
		if total_balance < 0:
			allow_negative = frappe.get_value("Leave Type", self.leave_type, "is_allow_negative")
			if not is_allow_negative:
				frappe.throw(_("Not enough Leave Credits {0}").format(self.total_leave_days))

	def validate_date(self):
		if self.from_date > self.to_date:
			frappe.throw(_("From Date must be before To Date"))

		from_exist = frappe.db.sql("""SELECT `name` FROM `tabLeave Application` 
			WHERE `name`!= %s AND employee = %s AND %s BETWEEN from_date AND to_date  """, (self.name, self.employee, self.from_date) )

		to_exist = frappe.db.sql("""SELECT `name` FROM `tabLeave Application` 
			WHERE `name`!= %s AND employee = %s AND %s BETWEEN from_date AND to_date  """, (self.name, self.employee, self.to_date) )

		if from_exist or to_exist:
			frappe.throw(_("A {0} is already Filed Within {1} to {2}").format(self.leave_type, self.from_date, self.to_date) )

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
		total_balance = 0
		bal = frappe.db.sql("""SELECT `name`, credits, used_credits, from_date, to_date FROM `tabLeave Balance` WHERE employee = %s 
			AND leave_type = %s AND (%s BETWEEN from_date AND to_date) AND (%s BETWEEN from_date AND to_date) """, (self.employee, self.leave_type, self.from_date, self.to_date), as_dict=True)

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
