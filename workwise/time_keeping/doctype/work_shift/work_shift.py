# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, string
from frappe import msgprint, _, scrub
from frappe.utils import cint, flt, getdate, cstr, nowdate, get_datetime_str, add_days
from datetime import time, datetime
from frappe.model.document import Document
from workwise.time_keeping.timekeeping_utils import chk_time_format, timediff_hrs, timediff_mins, str_datetime

class WorkShift(Document):
	def validate(self):
		self.validate_time_format()
		self.validate_time()
		#self.validate_pre_post()
		self.make_filter_name()

	def make_filter_name(self):
		self.filter_name = self.work_shift_type+" "+self.time_in+" - "+self.time_out
		if self.is_restday:
			self.filter_name = "RD "+self.time_in+" - "+self.time_out

	def validate_time_format(self):
		time_fds = ['time_in', 'time_out', 'break_start', 'break_end', 'nd_start', 'nd_end', 'pre_shift', 'post_shift']
		for fd in time_fds:
			chk_time_format(self.get(fd), "%H:%M:%S")
	
	def validate_time(self):
		if self.time_in > self.time_out:
			self.work_shift_type = "Night"
			time_in = get_datetime_str(self.time_in)
			time_out = add_days(get_datetime_str(self.time_out), 1)
			break_start = add_days(get_datetime_str(self.break_start), 1) if self.time_in > self.break_start else get_datetime_str(self.break_start)
			break_end = add_days(get_datetime_str(self.break_end), 1) if self.time_in > self.break_end else get_datetime_str(self.break_end)
			if break_end > time_out:
				frappe.throw("<b>BREAK END</b> must not be Greater than Time Out if Night Shift")
			
			if break_start > break_end:
				frappe.throw("<b>BREAK START</b> must not be Greater than Break End if Night Shift")

			work_hours = frappe.utils.data.time_diff_in_hours(time_out, time_in)
			break_mins = (frappe.utils.data.time_diff_in_seconds(break_end, break_start) / 60)		
		else:
			self.work_shift_type = "Day"
			if self.time_in > self.break_start or self.time_in > self.break_end or self.time_out < self.break_start or self.time_out < self.break_end:
				frappe.throw("<b>BREAK START</b> and <b>BREAK END</b> must be between Time In and Time Out")
			if self.break_start > self.break_end:
				frappe.throw("<b>BREAK START</b> must not be Greater than Break End if Day Shift")

			work_hours = frappe.utils.data.time_diff_in_hours(self.time_out, self.time_in)
			break_mins = (frappe.utils.data.time_diff_in_seconds(self.break_end, self.break_start) / 60)

		self.work_hours = work_hours - (break_mins / 60)
		self.break_mins = break_mins

	def get_working_hours(self):
		frappe.utils.data.time_diff_in_hours(self.break_start, self.break_end)

	def validate_pre_post(self):
		in_max_time = ['time_in', 'time_out', 'break_start', 'break_end']
		pre_shift = get_datetime_str(self.pre_shift)
		post_shift = get_datetime_str(self.post_shift)
		for fd in in_max_time:
			if self.get(fd):
				if pre_shift >= get_datetime_str(self.get(fd))<= post_shift:
					frappe.throw(_("( {0} ) Should Be Between Max Pre Shift and Max Post Shift").format( string.capwords(fd.replace("_"," ") ) ) )

	
	def delta_to_time(self, delta_obj):
		return (datetime.datetime.min + delta_obj).time()

@frappe.whitelist()
def calc_work_hours(time_in, time_out, break_start, break_end):
	chk_time_format(time_in, "%H:%M:%S")
	chk_time_format(time_out, "%H:%M:%S")
	fields_list = {
		"work_hours": timediff_hrs(time_in, time_out, "%H:%M:%S") - timediff_hrs(break_start, break_end, "%H:%M:%S"),
	}
	return fields_list

@frappe.whitelist()
def calc_break_mins(break_start, break_end):
	chk_time_format(break_start, "%H:%M:%S")
	chk_time_format(break_end, "%H:%M:%S")
	
	fields_list = {
		"break_mins": timediff_mins(break_start, break_end, "%H:%M:%S"),
	}
	return fields_list



