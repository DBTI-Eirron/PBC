# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe, datetime
from frappe.model.document import Document
from frappe	import _
from frappe.utils import flt, getdate, formatdate, cstr, nowdate, add_to_date
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_schedule, get_holiday_list, get_leave_list, get_all_dtrp, get_all_tla, 
get_shift_map, get_card_within, get_attendance, get_defaults, get_ob_list, get_ot_list, get_ut_list, get_ext_list, get_sorted_card, get_datetime)

class TimelogsOverride(Document):

	def override(self):
		self.validate_target_date()
		bio_id = frappe.get_value('Employee',self.employee,'biometrics_id')
		for d in self.get("timelogs_override"):
			self.save_work_shift(d,bio_id)
			self.save_time_logs(d,bio_id)
		frappe.msgprint(_("Time Logs Override Successful"),alert=True)

	def validate_target_date(self):
		for d in self.get("timelogs_override"):
			# max_ = datetime.datetime.strptime(d.target_date+ " 23:59", '%Y-%m-%d %H:%M')
			# if d.o_time_in:
			# 	target_time_out = datetime.datetime.strptime(d.o_time_in, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(days=1)
			# else:
			# 	target_time_out = get_datetime(d.time_in) + datetime.timedelta(days=1)
			shift_in, shift_out = frappe.get_value('Work Shift',d.work_shift,['time_in','time_out'])

			target_date = get_datetime(d.target_date+" "+str(shift_in))
			target_out = get_datetime(d.target_date+" "+str(shift_out))
			min_time_in = target_date - datetime.timedelta(days=1)
			max_time_in = target_date + datetime.timedelta(days=1)
			if shift_in > shift_out:
				min_time_out = target_out - datetime.timedelta(days=2)
				max_time_out = target_out + datetime.timedelta(days=2)
			else:
				min_time_out = target_out - datetime.timedelta(days=1)
				max_time_out = target_out + datetime.timedelta(days=1)




			if d.o_time_in and d.o_time_out:
				if get_datetime(d.o_time_in) > get_datetime(d.o_time_out):
					frappe.throw("Entry "+str(d.idx)+": Override time in sould be less than time out")
		
			if d.o_time_in:
				if get_datetime(d.o_time_in) <= min_time_in:
					frappe.throw("Entry "+str(d.idx)+": Override time in should be with in 24 hours before target date.")
				if get_datetime(d.o_time_in) >= max_time_in:
					frappe.throw("Entry "+str(d.idx)+": Override time in should be with in 24 hours after target date.")

			if d.o_time_out:
				if get_datetime(d.o_time_out) <= min_time_out:
					frappe.throw("Entry "+str(d.idx)+": Override time out should be with in 24 hours before target date.")
				if get_datetime(d.o_time_out) >= max_time_out:
					frappe.throw("Entry "+str(d.idx)+": Override time out should be with in 24 hours after target date.")

	def save_work_shift(self,d,bio_id):
		if d.old_shift != d.work_shift:		
			self.change_sched(d) 

	def save_time_logs(self,d,bio_id):
		override = frappe.db.sql("""SELECT `name` FROM `tabOverride List` WHERE employee = %s AND target_date = %s """, (self.employee, d.target_date), as_dict=True)
		for over in override:
			frappe.db.sql("""DELETE FROM `tabOverride List` WHERE `name` = %s""",(over.name),as_dict=True)
		if d.o_time_in or d.o_break_in or d.o_break_out or d.o_time_out:
			frappe.db.sql("""INSERT INTO `tabOverride List` (`name`, employee, target_date, time_in, break_in, break_out, time_out) VALUES (%s, %s, %s, %s, %s, %s, %s)""",(self.employee + " " + d.target_date,self.employee,d.target_date, d.o_time_in,d.o_break_in,d.o_break_out,d.o_time_out),as_dict=True)

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
				#"pre_shift": self.get_date(target_date, ws.pre_shift, ws.post_shift, ws.shift_type, 0),
				#"post_shift": self.get_date(target_date, ws.pre_shift, ws.post_shift, ws.shift_type, 1),							
				"break_start": self.get_date(target_date, ws.break_start, ws.break_end, ws.shift_type, 0),
				"break_end": self.get_date(target_date, ws.break_start, ws.break_end, ws.shift_type, 1),
				"nd_start": self.get_date(target_date, ws.nd_start, ws.time_out, ws.shift_type, 0),
				"nd_end": self.get_date(target_date, ws.nd_start, ws.time_out, ws.shift_type, 1),	
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
		override_list = self.get_override_list(pay_from,pay_to)
		entries = []
		for d in schedule:
			row = {
				"schedule_name": d['name'],
				"work_shift": d['work_shift'],
				"target_date": d['target_date'],
				"is_default": d['is_default_schedule'],
			}
			if str(d['target_date']) in override_list:
				row.update({
					"o_time_in": override_list[str(d['target_date'])]['time_in'],
					"o_break_in": override_list[str(d['target_date'])]['break_in'],
					"o_break_out": override_list[str(d['target_date'])]['break_out'],
					"o_time_out": override_list[str(d['target_date'])]['time_out'],
				})
			entries.append(row);

		for d in entries:
			row = self.append('timelogs_override', {})
			row.update(d)
		self.print_entries(pay_from,pay_to)

	def get_override_list(self,pay_from,pay_to):
		final_list = frappe._dict()
		override_list = frappe.db.sql("""SELECT * FROM `tabOverride List` WHERE employee = %s AND target_date BETWEEN %s and %s""",(self.employee,pay_from,pay_to),as_dict=True)
		for override in override_list:
			final_list.setdefault(str(override.target_date),frappe._dict({'time_in':override.time_in,'break_in':override.break_in,'break_out':override.break_out,'time_out':override.time_out}))
		return final_list

	def print_entries(self,pay_from,pay_to):
		emp_map = frappe._dict()
		emp_map.setdefault(self.employee, frappe._dict({
				"employee": self.employee,
				#"employee_name": emp.full_name,
				#"company": emp.company,
				#"employee_details": emp,
				"schedules": [],
				"timecards": [],
				"overrides": [],
				"hls": [],
				"lvs": [],
				"ots": [],
				"obs": [],
				"uts": [],
				"ext": [],
				"cto": [],
				"wss": [],
				"csa": [],
				"dtrp": [],
				"tla": [],
				"timelogs_map": {},
			})
		)

		emp = frappe.get_doc('Employee',self.employee)
		shift_map = get_shift_map()
		overrides = []
		bio_id = frappe.get_value('Employee',self.employee,'biometrics_id')
		timecard_list = get_timecard_list(bio_id, pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1))
		dtrp = self.get_dtrp(self.employee, pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1))
		tla = get_all_tla(emp_map, self.employee, pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1), 0, 0)
		emp_map[self.employee]['schedules'] = get_schedule(self.employee, pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1))

		for d in self.get("timelogs_override"):
			sched = {'target_date':d.target_date,'work_shift':d.work_shift,'is_default_schedule':d.is_default}
			entry = get_defaults(emp, sched, shift_map, overrides)
			cards_in, cards_out = get_card_within(entry, sched['target_date'], emp_map[self.employee]['timelogs_map'], emp_map[self.employee]['schedules'], 
				shift_map, entry.get('pre_shift'), entry.get('end_preshift'), entry.get('post_shift'), entry.get('end_postshift'), timecard_list, dtrp, tla)
			sorted_card_list = get_sorted_card(entry, cards_in, cards_out, emp_map[self.employee]['timelogs_map'])
			d.time_in = sorted_card_list['card_in']
			d.break_in = sorted_card_list['break_in']
			d.break_out = sorted_card_list['break_out']
			d.time_out = sorted_card_list['card_out']
			# d.o_time_in = sched['o_time_in']
			# d.o_break_in = sched['o_break_in']
			# d.o_break_out = sched['o_break_out']
			# d.o_time_out = sched['o_time_out']

	def get_dtrp(self, employee, pay_from, pay_to):
		dtr_apps = frappe.db.sql(""" SELECT DA.`name`, DA.`employee`, TIMESTAMP(DA.`target_date`, DT.`request`) as card_datetime, 
			DA.`target_date`, DT.`request`, DT.`type`, DA.`approved_on`, DT.`card_type`
			FROM `tabDTR Problem Table` DT INNER JOIN `tabDTR Problem Application` DA ON DT.`parent`=DA.`name` 
			WHERE DA.`workflow_state` = 'Approved' AND DA.employee = %s
			AND DA.`target_date` >= %s AND DA.`target_date` <= %s
			ORDER BY card_datetime """, (employee, pay_from, pay_to), as_dict=1)

		return dtr_apps