# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.utils import cint, flt, getdate, cstr, nowdate 
from frappe.model.document import Document
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs, sub_date, chk_time_format, timediff_hrs, timediff_mins, str_datetime

class OvertimeApplication(Document):
	def validate(self):
		self.validate_time_format()
		self.update_target_date()
		self.validate_date()
		self.calculate_totals()
		self.change_owner()
		self.get_recipients()
		self.validate_overtime()

	def on_submit(self):
		self.validate_approve_own_application()

	def on_cancel(self):
		self.validate_reject_cancel_own_application()

	def change_owner(self):
		owner = ""
		owner_email = frappe.db.sql("""SELECT user_id FROM `tabEmployee` WHERE `name` = %s LIMIT 1""",( self.employee ), as_dict=1)
		for d in owner_email:
			self.owner = d.user_id

	def validate_time_format(self):
		time_fds = ['from_time', 'to_time']
		for fd in time_fds:
			chk_time_format(str(self.get(fd)), "%H:%M:%S")

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

	def update_target_date(self):
		target_date = datetime.datetime.strptime(str(self.from_date) + ' ' + str(self.from_time), '%Y-%m-%d %H:%M:%S').date()
		#frappe.throw(_("{0}").format(nowdate()))
		if self.is_previous:
			self.target_date = target_date - datetime.timedelta(days=1)
		else:
			self.target_date = target_date

	def validate_date(self):
		from_date = datetime.datetime.strptime(str(self.from_date) + ' ' + str(self.from_time), '%Y-%m-%d %H:%M:%S').date()
		target_date = self.target_date
		
		new_from_date = datetime.datetime.strptime(str(self.from_date) + ' ' + str(self.from_time), '%Y-%m-%d %H:%M:%S').date()
		new_to_date = datetime.datetime.strptime(str(self.to_date) + ' ' + str(self.to_time), '%Y-%m-%d %H:%M:%S').date()

		if target_date != from_date and not self.is_previous:
			frappe.throw(_("From Date should be equal to Target Date"))

		if new_from_date > new_to_date:
			frappe.throw(_("From Date must be before To Date"))

	def calculate_totals(self):
		self.validate_time_format()
		#self.total_hrs = 0
		from_date = str(self.from_date) + ' ' + str(self.from_time)
		to_date = str(self.to_date) + ' ' + str(self.to_time)
		
		if from_date <= to_date:
			total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")
			self.total_hrs = total_hrs - flt(self.break_hrs, 8)
		else:
			if self.break_hrs:
				total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")
				self.total_hrs = total_hrs - flt(self.break_hrs, 8)
			else:
				total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")
				self.total_hrs = total_hrs

	def validate_overtime(self):
		ot_req_break = frappe.db.get_single_value('Timekeeping Settings', 'ot_req_break')
		if ot_req_break:
			if flt(self.total_hrs, 2) > flt(ot_req_break, 2) and flt(self.break_hrs, 	2) < 1:
				frappe.throw(_("Total Overtime hours is greater than {0} Break Time is required").format(ot_req_break))	

		ot_max_hours = frappe.db.get_single_value('Timekeeping Settings', 'ot_max_hours')
		if ot_max_hours:
			if flt(self.total_hrs, 2) > flt(ot_max_hours, 2):
				frappe.throw(_("Max Overtime hours per application is {0} , Did not save").format(ot_max_hours))	
				
	def validate_approve_own_application(self):
		cur_user = frappe.session.user
		if not "Administrator" in frappe.get_roles(cur_user):
			user_id = frappe.get_value("Employee", self.employee, "user_id")
			if user_id == frappe.session.user:
				frappe.throw(_("Not Allowed to Approved own Application"))

	def validate_reject_cancel_own_application(self):
		cur_user = frappe.session.user
		if not "Administrator" in frappe.get_roles(cur_user):
			user_id = frappe.get_value("Employee", self.employee, "user_id")
			if user_id == frappe.session.user:
				frappe.throw(_("You cannot reject or cancel your own application"))