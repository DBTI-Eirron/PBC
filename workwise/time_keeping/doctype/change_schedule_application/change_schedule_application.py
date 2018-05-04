# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document

class ChangeScheduleApplication(Document):
	def on_validate(self):
		self.change_owner()
		self.get_recipients()
		
	def on_submit(self):
		self.change_sched()

	def on_cancel(self):
		self.revert_sched()


	def change_owner(self):
		owner = ""
		owner_email = frappe.db.sql("""SELECT user_id FROM `tabEmployee` WHERE `name` = %s LIMIT 1""",( self.employee ), as_dict=1)
		for d in owner_email:
			self.owner = d.user_id

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

	def change_sched(self):
		work_shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(self.new_shift), as_dict=True)
		old_shift = ""
		exist = frappe.db.sql("""SELECT `name` FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (self.employee, self.target_date), as_dict=True)
		if exist:
			frappe.db.sql("""DELETE FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (self.employee, self.target_date), as_dict=True)
			old_shift = frappe.db.sql_list("""SELECT `work_shift` FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s LIMIT 1""", (self.employee, self.target_date))
		target_date = getdate(self.target_date)		
		for ws in work_shift:
			work_sched = frappe.new_doc("Work Schedule")
			work_sched.update({
				"employee": self.employee,
				"company": self.company,
				"target_date": target_date,
				"work_shift": self.new_shift,
				"datetime_in": self.get_date(target_date, ws.time_in, ws.time_out, ws.shift_type, 0),
				"datetime_out": self.get_date(target_date, ws.time_out, ws.time_out, ws.shift_type, 1),
				"pre_shift": self.get_date(target_date, ws.pre_shift, ws.post_shift, ws.shift_type, 0),
				"post_shift": self.get_date(target_date, ws.pre_shift, ws.post_shift, ws.shift_type, 1),							
				"break_start": self.get_date(target_date, ws.break_start, ws.break_end, ws.shift_type, 0),
				"break_end": self.get_date(target_date, ws.break_start, ws.break_end, ws.shift_type, 1),
				"half_in": self.get_date(target_date, ws.half_time_in, ws.half_time_out, ws.shift_type, 0),
				"half_out": self.get_date(target_date, ws.half_time_in, ws.half_time_out, ws.shift_type, 1),
				"nd_start": self.get_date(target_date, ws.nd_start, ws.nd_end, ws.shift_type, 0),
				"nd_end": self.get_date(target_date, ws.nd_start, ws.nd_end, ws.shift_type, 1),	
				"shift_type": ws.shift_type,
				"is_restday": ws.is_restday,
				"is_flexible": ws.is_flexible,
			})	
			if work_sched.insert():
				if old_shift:
					self.old_shift = old_shift
			else:
				frappe.throw(_("Changing Failed"))

	def revert_sched(self):
		work_shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(self.old_shift), as_dict=True)
		
		exist = frappe.db.sql("""SELECT `name` FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (self.employee, self.target_date), as_dict=True)
		if exist:
			frappe.db.sql("""DELETE FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (self.employee, self.target_date), as_dict=True)
	
		target_date = getdate(self.target_date)		
		for ws in work_shift:
			work_sched = frappe.new_doc("Work Schedule")
			work_sched.update({
				"employee": self.employee,
				"company": self.company,
				"target_date": target_date,
				"work_shift": self.new_shift,
				"datetime_in": self.get_date(target_date, ws.time_in, ws.time_out, ws.shift_type, 0),
				"datetime_out": self.get_date(target_date, ws.time_out, ws.time_out, ws.shift_type, 1),
				"pre_shift": self.get_date(target_date, ws.pre_shift, ws.post_shift, ws.shift_type, 0),
				"post_shift": self.get_date(target_date, ws.pre_shift, ws.post_shift, ws.shift_type, 1),							
				"break_start": self.get_date(target_date, ws.break_start, ws.break_end, ws.shift_type, 0),
				"break_end": self.get_date(target_date, ws.break_start, ws.break_end, ws.shift_type, 1),
				"half_in": self.get_date(target_date, ws.half_time_in, ws.half_time_out, ws.shift_type, 0),
				"half_out": self.get_date(target_date, ws.half_time_in, ws.half_time_out, ws.shift_type, 1),
				"nd_start": self.get_date(target_date, ws.nd_start, ws.nd_end, ws.shift_type, 0),
				"nd_end": self.get_date(target_date, ws.nd_start, ws.nd_end, ws.shift_type, 1),	
				"shift_type": ws.shift_type,
				"is_restday": ws.is_restday,
				"is_flexible": ws.is_flexible,
			})	
			if work_sched.insert():
				if old_shift:
					self.old_shift = old_shift
			else:
				frappe.throw(_("Changing Failed"))

	def get_date(self, date, start, end, type, is_end):
		if is_end == 1:
			if self.delta_to_time(start) > self.delta_to_time(end):
				dt = (datetime.datetime.combine( date, self.delta_to_time(end) ) + datetime.timedelta(days=1) ).strftime('%Y-%m-%d %H:%M:%S')
			else:
				dt = datetime.datetime.combine( date, self.delta_to_time(end) ).strftime('%Y-%m-%d %H:%M:%S') 
		else:
			dt = datetime.datetime.combine( date, self.delta_to_time(start) ).strftime('%Y-%m-%d %H:%M:%S') 
	
		return dt

	def delta_to_time(self, delta_obj):
		return (datetime.datetime.min + delta_obj).time()


	def get_shift(self):
		fields_list = {}
		old_shift =  frappe.db.sql("""SELECT `name`, work_shift FROM `tabWork Schedule` WHERE employee=%s and target_date = %s LIMIT 1""",(self.employee, self.target_date), as_dict=True);
		
		for os in old_shift:
			fields_list = {"old_shift": os.work_shift }
		
		if fields_list:
			return fields_list