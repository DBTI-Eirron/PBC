# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe, datetime
from frappe.model.document import Document
from frappe	import _
from frappe.utils import flt, getdate, formatdate, cstr, nowdate, add_to_date
from workwise.time_keeping.attendance_utils import get_timecard_list, get_schedule, get_holiday_list, get_leave_list, get_shift_map, get_card_within, get_attendance, get_card_within,get_datetime,get_shift_map

class TimelogsOverride(Document):

	def override(self):
		for d in self.get("timelogs_override"):
			schedule_in = frappe.get_value('Work Shift',d.work_shift,'time_in')
			if d.time_in:
				if d.log_time_in:
					frappe.set_value('Time Card',d.log_time_in,'time',d.time_in)
				else:
					self.new_time_card(bio_id,0,d.target_date,d.time_in)
			else:
				if d.time_in:
					frappe.delete_doc("Time Card", d.log_time_in)
			if d.break_in:
				if d.log_break_in:
					frappe.set_value('Time Card',d.log_break_in,'time',d.break_in)
				else:
					self.new_time_card(bio_id,2,d.target_date,d.break_in)
			else:
				if d.log_break_in:
					frappe.delete_doc("Time Card", d.log_break_in)
			if d.break_out:
				if d.log_break_out:
					frappe.set_value('Time Card',d.log_break_out,'time',d.break_out)
				else:
					self.new_time_card(bio_id,3,d.target_date,d.break_out)
			else:
				if d.log_break_out:
					frappe.delete_doc("Time Card", d.log_break_out)
			if d.time_out:
				if d.log_time_out:
					frappe.set_value('Time Card',d.log_time_out,'time',d.time_out)
				else:
					bio_id = frappe.get_value('Employee',self.employee,'biometrics_id')
					shift_map = get_shift_map()
					time_in = frappe.get_value('Work Shift',d.work_shift,'time_in')
					date_time_in = str(d.target_date) + " " + str(time_in)
					pre_shift = add_to_date(get_datetime(date_time_in), hours= (0 - shift_map[d.work_shift]['setup_preshift']) )
					time_out = datetime.datetime.strptime(d.time_out, '%H:%M:%S').time()
					str_pre_shift = str(pre_shift)[11:]
					final_pre_shift = datetime.datetime.strptime(str_pre_shift, '%H:%M:%S').time()
					if time_out < final_pre_shift:
						date = getdate(d.target_date) + datetime.timedelta(days=1) 
						self.new_time_card(bio_id,1,str(date),d.time_out)
					else:
						self.new_time_card(bio_id,1,d.target_date,d.time_out)
			else:
				if d.log_time_out:
					frappe.delete_doc("Time Card", d.log_time_out)

		frappe.msgprint(_("Time Logs Override Successful"),alert=True)

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
		pay_from, pay_to = frappe.db.get_value("Payroll Period", self.payroll_period, ["from_date", "to_date"])
		schedule = get_schedule(self.employee, pay_from, pay_to)
		if schedule:
			entries = []
			for d in schedule:
				row = {
					"work_shift": d.work_shift,
					"target_date": d.target_date
				}
				entries.append(row);

			for d in entries:
				row = self.append('timelogs_override', {})
				row.update(d)

		tc_entries = self.load_entries(pay_from,pay_to)
		self.print_entries(tc_entries,pay_from,pay_to)


	def load_entries(self,pay_from,pay_to):
		entries = []
		bio_id = frappe.get_value('Employee',self.employee,'biometrics_id')
		tc_entries = frappe.db.sql("""SELECT `name`,`card_type`, `time`, `date` FROM `tabTime Card` WHERE `biometrics_id`=%s AND `date` >= %s and `date`<=%s""", (bio_id,pay_from,pay_to),as_dict=True)
		#for d in tc_entries:
		#	row = {
		#		'name': d.name,
		#		'card_type': d.card_type,
		#		'time': d.time,
		#		'date': d.date,
		#		'date_time': str(d.date)+ " " +str(d.time)
		#	}
		#	entries.append(row);

		return tc_entries

	def  print_entries(self,tc_entries,pay_from,pay_to):
		
		for d in self.get("timelogs_override"):
			bio_id = frappe.get_value('Employee',self.employee,'biometrics_id')
			timecard_list = get_timecard_list(bio_id, pay_from, pay_to + datetime.timedelta(days=1))
			shift_map = get_shift_map()
			time_in = frappe.get_value('Work Shift',d.work_shift,'time_in')
			time_out = frappe.get_value('Work Shift',d.work_shift,'time_out')
			date_time_in = str(d.target_date) + " " + str(time_in)
			date_time_out = str(d.target_date) + " " + str(time_out)
			pre_shift = add_to_date(get_datetime(date_time_in), hours= (0 - shift_map[d.work_shift]['setup_preshift']) )
			post_shift = add_to_date(get_datetime(date_time_out), hours=shift_map[d.work_shift]['setup_postshift'])
			final_pre_shift = pre_shift + datetime.timedelta(days=1)
			for x in tc_entries:
				final_date_time = get_datetime(str(x.date)+ " " +str(x.time))
				if final_date_time < final_pre_shift and  final_date_time > pre_shift:
					if  x.card_type == 0:
						d.log_time_in = x.name
						d.time_in = x.time
					if x.card_type == 1:
						d.log_time_out = x.name
						d.time_out = x.time
					if x.card_type == 2:
						d.log_break_in = x.name
						d.break_in = x.time
					if x.card_type == 3:
						d.log_break_out = x.name
						d.break_out = x.time

			
			

		
