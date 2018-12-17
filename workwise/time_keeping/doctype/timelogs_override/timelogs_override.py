# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe, datetime
from frappe.model.document import Document
from frappe	import _
from frappe.utils import flt, getdate, formatdate, cstr, nowdate, add_to_date
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_schedule, get_holiday_list, get_leave_list, 
get_shift_map, get_card_within, get_attendance, get_defaults, get_ob_list, get_ot_list, get_ut_list, get_ext_list, get_sorted_card, get_datetime)

class TimelogsOverride(Document):

	def override(self):
		bio_id = frappe.get_value('Employee',self.employee,'biometrics_id')
		for d in self.get("timelogs_override"):
			self.save_work_shift(d,bio_id)
			self.save_time_logs(d,bio_id)
		frappe.msgprint(_("Time Logs Override Successful"),alert=True)

	def save_work_shift(self,d,bio_id):
		if d.old_shift != d.work_shift:		
			self.change_sched(d) 

	def save_time_logs(self,d,bio_id):
		for item in self.get("timelogs_override"):
			schedule = frappe.db.sql("""SELECT `name` FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (self.employee, d.target_date), as_dict=True)
			for sched in schedule:
				frappe.db.sql("""UPDATE `tabWork Schedule`
				SET o_time_in = %s, o_break_in = %s, o_break_out =%s, o_time_out =%s
				WHERE `name` =%s""",(d.o_time_in,d.o_break_in,d.o_break_out,d.o_time_out,sched.name),as_dict=True)
			
	
	def change_sched(self,d):
		work_shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(d.work_shift), as_dict=True)
		exist = frappe.db.sql("""SELECT `name` FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (self.employee, d.target_date), as_dict=True)
		if exist:
			frappe.db.sql("""DELETE FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (self.employee, d.target_date), as_dict=True)
		target_date = getdate(d.target_date)		

		for ws in work_shift:
			work_sched = frappe.new_doc("Work Schedule")
			work_sched.update({
				"work_hours":ws.work_hours,
				"break_mins":ws.break_mins,
				"employee": self.employee,
				"company": self.company,
				"target_date": target_date,
				"work_shift": d.work_shift,
				"datetime_in": self.get_date(target_date, ws.time_in, ws.time_out, ws.shift_type, 0),
				"datetime_out": self.get_date(target_date, ws.time_in, ws.time_out, ws.shift_type, 1),
				"pre_shift": self.get_date(target_date, ws.pre_shift, ws.post_shift, ws.shift_type, 0),
				"post_shift": self.get_date(target_date, ws.pre_shift, ws.post_shift, ws.shift_type, 1),							
				"break_start": self.get_date(target_date, ws.break_start, ws.break_end, ws.shift_type, 0),
				"break_end": self.get_date(target_date, ws.break_start, ws.break_end, ws.shift_type, 1),
				"nd_start": self.get_date(target_date, ws.nd_start, ws.nd_end, ws.shift_type, 0),
				"nd_end": self.get_date(target_date, ws.nd_start, ws.nd_end, ws.shift_type, 1),	
				"shift_type": ws.shift_type
			})
			work_sched.insert()
			work_sched.save()

			d.old_shift = d.work_shift

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

	def new_time_card(self,bio_id,card_type,date,time):
		new_timecard = frappe.new_doc("Time Card")
		new_timecard.update({
				"biometrics_id": bio_id,
				"card_type": card_type,
				"date": date,
				"time": time
			})
		new_timecard.insert()
		new_timecard.save()

	def load_work_schedule(self):
		schedule = []
		bio_id = frappe.get_value('Employee',self.employee,'biometrics_id')
		pay_from, pay_to = frappe.db.get_value("Payroll Period", self.payroll_period, ["attendance_from", "attendance_to"])
		schedule = get_schedule(self.employee, pay_from, pay_to)
		entries = []
		for d in schedule:
			row = {
				"schedule_name": d.name,
				"work_shift": d.work_shift,
				"old_shift": d.work_shift,
				"target_date": d.target_date,
				"o_time_in":d.o_time_in,
				"o_break_in":d.o_break_in,
				"o_break_out":d.o_break_out,
				"o_time_out":d.o_time_out
			}
			entries.append(row);

		for d in entries:
			row = self.append('timelogs_override', {})
			row.update(d)
		self.print_entries(pay_from,pay_to)

	def  print_entries(self,pay_from,pay_to):
		for d in self.get("timelogs_override"):
			employee = frappe.db.sql("""SELECT * FROM `tabEmployee` WHERE `name`= %s LIMIT 1""",(self.employee),as_dict=True)
			for emp in employee:
				bio_id = frappe.get_value('Employee',self.employee,'biometrics_id')
				timecard_list = get_timecard_list(bio_id, pay_from, pay_to + datetime.timedelta(days=1))
				shift_map = get_shift_map()
				schedule = frappe.db.sql("""SELECT * FROM `tabWork Schedule` WHERE employee = %s AND target_date =%s""",(self.employee,d.target_date),as_dict=True)
				for sched in schedule:
					entry = get_defaults(emp, sched, shift_map)
					datetime_in = sched['datetime_in']
					datetime_out = sched['datetime_out']
					setup_preshift, end_preshift, setup_postshift, end_postshift = frappe.get_value('Work Shift',d.work_shift,['setup_preshift','end_preshift','setup_postshift','end_postshift'])
					pre_shift = datetime_in - datetime.timedelta(hours=setup_preshift)
					end_pre_shift = datetime_in + datetime.timedelta(hours=end_preshift)
					post_shift = datetime_out - datetime.timedelta(hours=setup_postshift)
					end_post_shift = datetime_out + datetime.timedelta(hours=end_postshift)
					cards_in, cards_out = get_card_within(pre_shift, end_pre_shift, post_shift, end_post_shift, timecard_list)
					sorted_card_list = get_sorted_card(entry, cards_in, cards_out)
					d.time_in = sorted_card_list['card_in']
					d.break_in = sorted_card_list['break_in']
					d.break_out = sorted_card_list['break_out']
					d.time_out = sorted_card_list['card_out']
					# d.o_time_in = sched['o_time_in']
					# d.o_break_in = sched['o_break_in']
					# d.o_break_out = sched['o_break_out']
					# d.o_time_out = sched['o_time_out']


					
					

			
