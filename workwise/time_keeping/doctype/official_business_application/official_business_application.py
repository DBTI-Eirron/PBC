# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.utils import cint, flt, getdate, cstr, nowdate, get_datetime, add_days, get_datetime_str, get_time
from frappe.model.document import Document
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs, sub_date, timediff_hrs
from workwise.time_keeping.application_utils import grant_head_subordinate_access, get_approver_and_date, validate_approve_own_application, validate_reject_cancel_own_application, change_owner

class OfficialBusinessApplication(Document):
	def validate(self):
		grant_head_subordinate_access(self)
		self.get_ob_hrs()
		change_owner(self)
		self.get_recipients()
		#self.change_time()

	def on_submit(self):
		validate_approve_own_application(self)
		get_approver_and_date(self)

	def on_cancel(self):
		validate_reject_cancel_own_application(self)

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

	def get_ob_hrs(self):
		total_ob_time = 0
		for d in self.get('official_business_application_table'):
			total_hrs = 0
			if get_time(d.from_time) > get_time(d.to_time):
				from_date = get_datetime(str(d.target_date)+" "+str(d.from_time))
				to_date = get_datetime(str(add_days(d.target_date, 1))+" "+str(d.from_time))
			else:
				from_date = get_datetime(str(d.target_date)+" "+str(d.from_time))
				to_date = get_datetime(str(d.target_date)+" "+str(d.to_time))
				
			if not d.is_excluded == 1:
				total_hrs = abs(((from_date - to_date).total_seconds()) / 60 /60)
				total_ob_time += total_hrs
				d.hrs = total_hrs
		self.total_hrs = total_ob_time

	def get_ob_dates(self):
		total_balance = 0
		self.set('official_business_application_table', [])
		if not self.from_date:
			frappe.throw(_("No From Date"))

		if not self.to_date:
			frappe.throw(_("No To Date"))
		
		if self.from_date > self.to_date:
			frappe.throw(_("To From Date Should be Greater than To"))
			
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
			        "from_time": "00:00:00",
			        "to_time": "00:00:00",
			        "is_holiday": self.chk_holiday(i),
			        "is_excluded": 0
			    }
			    
			    official_business_application_table.append(info);
			
			entries = sorted(list(official_business_application_table), 
				key=lambda k: k['target_date'])		    

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
				
	def chk_holiday(self, target_date):
		holiday_tag  = 0
		location = frappe.get_value("Employee", self.employee, "location")

		holiday = frappe.db.sql("""SELECT `name` FROM `tabHoliday` WHERE holiday_date = %s 
			AND company = %s AND location = %s """, (target_date, self.company, location), as_dict=True)

		if holiday:
			holiday_tag = 1

		return holiday_tag 

	def make_new_ob_app(self):
		ob_list = frappe.db.sql("""SELECT * FROM `tabOfficial Business Application`""", as_dict=True)
		for d in ob_list:
			frappe.db.sql("""INSERT INTO `tabOfficial Business Application Table` 
				( target_date, from_time, to_time, is_half_day, is_holiday, is_excluded, parent, parentfield, parenttype, modified_by, owner, creation, modified, `name`,docstatus) 
				VALUES (%s,%s,%s,0,0,0,%s,"official_business_application_table","Official Business Application","Administrator","Administrator",NOW(),NOW(),%s,1)""", (d.from_date,d.from_time,d.to_time,d.name,d.name))

@frappe.whitelist()
def update_old_obs():
	unupdated_list = frappe.db.sql(""" SELECT `name`,to_time, from_time, travel_time, from_date, total_hrs FROM `tabOfficial Business Application` 
		WHERE `name` NOT IN (SELECT DISTINCT(parent) FROM `tabOfficial Business Application Table`) AND docstatus != 2 """, as_dict=True)
	
	for d in unupdated_list:
		oba = frappe.get_doc("Official Business Application", d.name)
		oba.append("official_business_application_table", {
			"target_date": d.from_date,
			"from_time": d.from_time,
			"to_time": d.to_time,	
			"travel_time": d.travel_time,
			"hrs": d.total_hrs,
		})
		oba.save()