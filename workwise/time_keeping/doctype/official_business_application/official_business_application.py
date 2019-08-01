# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.utils import cint, flt, getdate, cstr, nowdate, get_datetime, add_days, get_datetime_str, get_time
from frappe.model.document import Document
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs, sub_date, timediff_hrs
from workwise.time_keeping.application_utils import ( grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, 
change_owner, get_levelled_approval, get_levelled_approval_rejection, clear_approval_history, validate_inactive_employee, get_approver_email_list, get_cancelled_by_and_date )

class OfficialBusinessApplication(Document):
	def validate(self):
		validate_inactive_employee(self)
		clear_approval_history(self)
		self.validate_date()
		grant_head_subordinate_access(self)
		self.get_ob_hrs()
		self.get_target_date()
		change_owner(self)
		self.get_recipients()
		#self.change_time()

	def on_submit(self):
		validate_approve_own_application(self)
		get_approver_and_date(self)
		get_approver_email_list(self, 'on_submit')

	def before_update_after_submit(self):
		get_approver_email_list(self, 'before_update_after_submit')
		get_levelled_approval(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)
		get_levelled_approval_rejection(self)
		get_cancelled_by_and_date(self)

	def get_target_date(self):
		for d in self.get('official_business_application_table'):
			if d.is_previous == 1:
				d.target_date = getdate(d.date) - datetime.timedelta(days=1)
			else:
				d.target_date = d.date

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

		if self.total_hrs == 0:
			frappe.throw(_("<b>Official Business Application: {0}</b><hr> Total Hours must not be zero").format(self.name))

	def get_ob_hrs(self):
		total_ob_time = 0
		for d in self.get('official_business_application_table'):
			total_hrs = 0
			#if get_time(d.from_time) > get_time(d.to_time):
			from_date = get_datetime(str(d.date)+" "+str(d.from_time))
			to_date = get_datetime(str(d.to_date)+" "+str(d.to_time))
			#else:
			#	from_date = get_datetime(str(d.date)+" "+str(d.from_time))
			#	to_date = get_datetime(str(d.date)+" "+str(d.to_time))
				
			if not d.is_excluded == 1:
				total_hrs = abs(((from_date - to_date).total_seconds()) / 60 /60)
				total_ob_time += total_hrs
				d.hrs = total_hrs
		self.total_hrs = total_ob_time

	def validate_date(self):
		if self.from_date > self.to_date:
			frappe.throw(_("<b>Official Business Application: {0}</b><hr> From date must be before To date").format(self.name))

	def get_ob_dates(self):
		total_balance = 0
		self.set('official_business_application_table', [])
		if not self.from_date:
			frappe.throw(_("<b>Official Business Application: {0}</b><hr> No From Date").format(self.name))

		if not self.to_date:
			frappe.throw(_("<b>Official Business Application: {0}</b><hr> No To Date").format(self.name))
		
		if self.from_date > self.to_date:
			frappe.throw(_("<b>Official Business Application: {0}</b><hr> From date must be before To date").format(self.name))
			
		else:
			entries = [];
			dates = [];
			official_business_application_table = [];

			start = datetime.datetime.strptime(str(self.from_date), '%Y-%m-%d')
			end = datetime.datetime.strptime(str(self.to_date), '%Y-%m-%d')
			step = datetime.timedelta(days=1)
			
			while start <= end:
			    dates.append(start.date());
			    start += step
			    
			for i in dates:
			    info = {
				    "target_date": i,
			        "date": i,
			        "to_date": i,
			        "from_time": "00:00:00",
			        "to_time": "00:00:00",
			        "is_holiday": self.chk_holiday(i),
			        "is_excluded": 0,
			        "is_previous": 0
			    }
			    
			    official_business_application_table.append(info);
			
			entries = sorted(list(official_business_application_table), 
				key=lambda k: k['date'])		    

			self.set('official_business_application_table', [])
			
			for d in entries:
				row = self.append('official_business_application_table', {})
				row.update(d)

	def change_time(self):
		for d in self.get('official_business_application_table'):
			#if d.from_time == "0:00:00" or d.from_time ==  "00:00:00":
			d.from_time = self.from_time
			
			#if d.to_time == "0:00:00" or d.to_time == "00:00:00":
			d.to_time = self.to_time
				
	def chk_holiday(self, date):
		holiday_tag  = 0
		location = frappe.get_value("Employee", self.employee, "location")

		holiday = frappe.db.sql("""SELECT `name` FROM `tabHoliday` WHERE holiday_date = %s 
			AND company = %s AND location = %s """, (date, self.company, location), as_dict=True)

		if holiday:
			holiday_tag = 1

		return holiday_tag 

	def validate_application(self):
		exist = frappe.db.sql("""SELECT `parent` FROM `tabOfficial Business Application Table` WHERE (target_date BETWEEN %s AND %s) AND parent != %s AND docstatus = 1 """, ( self.from_date, self.to_date, self.name), as_dict=True)

		if exist:
			frappe.throw(_("<b>Official Business Application: {0}</b><hr> Application already exists: {1}").format(self.name, exist[0].parent))

@frappe.whitelist()
def update_old_obs():
	unupdated_list = frappe.db.sql(""" SELECT `name`,to_time, from_time, travel_time, from_date, total_hrs FROM `tabOfficial Business Application` 
		WHERE `name` NOT IN (SELECT DISTINCT(parent) FROM `tabOfficial Business Application Table`) AND docstatus != 2 """, as_dict=True)
	
	for d in unupdated_list:
		oba = frappe.get_doc("Official Business Application", d.name)
		oba.append("official_business_application_table", {
			"travel_time": d.travel_time,
			"hrs": d.hrs,
			"target_date": d.target_date,
	        "date": d.date,
	        "from_time": d.from_time,
	        "to_time": d.to_time,
	        "is_holiday": d.is_holiday,
	        "is_excluded": d.is_excluded,
	        "is_previous": d.is_previous
		})
		oba.save()