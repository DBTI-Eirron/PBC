# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, cstr
from frappe import _
from frappe.model.document import Document
from workwise.employee_201.utils_empget import empget_employees, empget_subordinates, empget_company

class WorkScheduleAssignment(Document):
	def assign_schedule(self):
		self.check_permission('write')
		ss_list = []

		if not self.from_date or not self.to_date:
			frappe.throw(_("From Date and To Date Required"))

		if self.apply_template:
			ss_list = self.assign_schedule_template()
		else:
			frappe.throw(_("Select Template"))

		return self.create_log(ss_list)

	def assign_schedule_template(self):
		sched_map = self.get_sched_template()
		dates = []
		date_list = []
		ss_list = []
		start = datetime.datetime.strptime(self.from_date, '%Y-%m-%d')
		end = datetime.datetime.strptime(self.to_date, '%Y-%m-%d')
		step = datetime.timedelta(days=1)
		
		while start <= end:
			date_list.append(start.date())
			start += step

		for i in date_list:
			day = datetime.datetime.strptime(str(i), '%Y-%m-%d').strftime('%A').lower()
			info = {
				"date": i,
				"day": day,
				"work_shift": sched_map[day]['work_shift'],
				"shift_type": sched_map[day]['shift_type'],
				"work_hours": sched_map[day]['work_hours'],
				"break_mins": sched_map[day]['break_mins'],
				"datetime_in": self.get_date(i, sched_map[day]['time_in'], sched_map[day]['time_out'], sched_map[day]['shift_type'], 0),
				"datetime_out": self.get_date(i, sched_map[day]['time_out'], sched_map[day]['time_out'], sched_map[day]['shift_type'], 1),
				"break_start": self.get_date(i, sched_map[day]['break_start'], sched_map[day]['break_end'], sched_map[day]['shift_type'], 0),
				"break_end": self.get_date(i, sched_map[day]['break_start'], sched_map[day]['break_end'], sched_map[day]['shift_type'], 1),
				"nd_start": self.get_date(i, sched_map[day]['nd_start'], sched_map[day]['nd_end'], sched_map[day]['shift_type'], 0),
				"nd_end": self.get_date(i, sched_map[day]['nd_start'], sched_map[day]['nd_end'], sched_map[day]['shift_type'], 1),	
			}
			info["pre_shift"] = add_to_date(info["datetime_in"], hours= (0 - sched_map[day]['setup_preshift']) )
			info["post_shift"] = add_to_date(info["datetime_out"], hours=sched_map[day]['setup_postshift'])
			
			dates.append(info)

		if self.get('employees'):
			for emp in self.get('employees'):
				company = frappe.db.get_value("Employee", emp.employee, "company")
				exist = frappe.db.sql("""SELECT `name` FROM `tabWork Schedule` WHERE employee = %s AND target_date >= %s AND target_date <= %s LIMIT 1""", (emp.employee, self.from_date, self.to_date), as_dict=True)
				if exist:
					exist = frappe.db.sql("""DELETE FROM `tabWork Schedule` WHERE employee = %s AND target_date >= %s AND target_date <= %s """, (emp.employee, self.from_date, self.to_date), as_dict=True)

				for d in dates:
					work_sched = frappe.new_doc("Work Schedule")
					work_sched.update({
						"employee": emp.employee,
						"company": company,
						"target_date": d["date"],
						"work_shift": d["work_shift"],
						"shift_type": d["shift_type"],
						"work_hours": d['work_hours'],
						"break_mins": d['break_mins'],
						"datetime_in": d["datetime_in"],
						"datetime_out": d["datetime_out"],
						"pre_shift": d["pre_shift"],
						"post_shift": d["post_shift"],							
						"break_start": d["break_start"],
						"break_end": d["break_end"],
						"nd_start": d["nd_start"],
						"nd_end": d["nd_end"],
					})	
					work_sched.insert()
					label = "Assigned Schedule " + cstr(emp.employee_name) +""
				ss_list.append(label)
		else:
			frappe.throw(_("No Employee Found"))
		
		return ss_list

	def create_log(self, ss_list):
		log = "<p>" + _("No Employee for the above selected criteria Created") + "</p>"
		if ss_list:
			log = "<b>" + _("Schedule Created") + "</b><br><br>%s" % '<br>'.join(ss_list)
		return log

	def format_as_links(self, ss_list):
		return ['<a href="#Form/Salary Slip/{0}">{0}</a>'.format(s) for s in ss_list]

	def delta_to_time(self, delta_obj):
		return (datetime.datetime.min + delta_obj).time()

	def get_date(self, date, start, end, type, is_end):
		if is_end == 1:
			if self.delta_to_time(start) > self.delta_to_time(end):
				dt = (datetime.datetime.combine(date, self.delta_to_time(end) ) + datetime.timedelta(days=1) ).strftime('%Y-%m-%d %H:%M:%S')
			else:
				dt = datetime.datetime.combine(date, self.delta_to_time(end) ).strftime('%Y-%m-%d %H:%M:%S') 
		else:
			dt = datetime.datetime.combine(date, self.delta_to_time(start) ).strftime('%Y-%m-%d %H:%M:%S') 
	
		return dt

	def get_sched_template(self):
		sched_template = {}
		sched = frappe.db.sql("""SELECT * FROM `tabWork Schedule Template` WHERE `name` = %s LIMIT 1""",(self.apply_template), as_dict=1)
		days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
		for day in days:
			shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(sched[0][day]), as_dict=1)
			sched_template[day] = {
				"work_shift": shift[0]['name'],
				"work_hours": shift[0]['work_hours'],
				"break_mins": shift[0]['break_mins'],
				"time_in": shift[0]['time_in'],
				"time_out": shift[0]['time_out'],				
				"break_start": shift[0]['break_start'],
				"break_end": shift[0]['break_end'],
				"nd_start": shift[0]['nd_start'],
				"nd_end": shift[0]['nd_end'],				
				"shift_type": shift[0]['work_shift_type'],
				"pre_shift": shift[0]['pre_shift'],
				"post_shift": shift[0]['post_shift'],
				"setup_preshift": shift[0]['setup_preshift'],
				"setup_postshift": shift[0]['setup_postshift'],
			}

		return sched_template

	def filter_reset(self):
		self.set('employees', [])

	def filter_subordinates(self):
		entries = []
		curr_emp = []
		employees = empget_subordinates(frappe.session.user)

		for emp in self.employees:
			curr_emp.append(emp.employee)

		if employees:
			for d in employees:
				if d.name not in curr_emp:
					row = {
						"employee": d.name,
						"employee_name": d.full_name,
					}
					entries.append(row)

			for d in entries:
				row = self.append('employees', {})
				row.update(d)

	def filter_company(self):
		if not self.company:
			frappe.throw(_("Company is Required"))

		entries = []
		curr_emp = []
		employees = empget_company(self.company)

		for emp in self.employees:
			curr_emp.append(emp.employee)

		if employees:
			for d in employees:
				if d.name not in curr_emp:
					row = {
						"employee": d.name,
						"employee_name": d.full_name,
					}
					entries.append(row)

			for d in entries:
				row = self.append('employees', {})
				row.update(d)

	def filter_add(self):
		if not self.company:
			frappe.throw(_("Company is Required"))

		if self.filter_value and self.filter_type:
			entries = []
			curr_emp = []
			employees = empget_employees(self.filter_type, self.filter_value, self.company)
			
			for emp in self.employees:
				curr_emp.append(emp.employee)

			if employees:
				for d in employees:
					if d.name not in curr_emp:
						row = {
							"employee": d.name,
							"employee_name": d.full_name,
						}
						entries.append(row)

				for d in entries:
					row = self.append('employees', {})
					row.update(d)
		else:
			frappe.throw(_(" Input Filter Value and Filter Type "))

