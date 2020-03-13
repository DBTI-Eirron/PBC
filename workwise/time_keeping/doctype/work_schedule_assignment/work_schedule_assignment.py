# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, cstr
from frappe import _
from frappe.model.document import Document
from workwise.employee_201.emp_filters_utils import empget_employees, empget_subordinates, empget_company
from workwise.time_keeping.application_utils import get_user_fullname

class WorkScheduleAssignment(Document):
	def assign_schedule(self):
		self.validate_fields()
		self.validate_inactive_employee()
		self.validate_self_scheduling()
		self.check_permission('write')
		ss_list = self.assign_employee_schedule()
		self.create_assignment_logs()

		return self.create_log(ss_list)

	def assign_employee_schedule(self):
		ss_list = []
		employee_entry = []
		date_list = []
		start = datetime.datetime.strptime(self.from_date, '%Y-%m-%d')
		end = datetime.datetime.strptime(self.to_date, '%Y-%m-%d')
		step = datetime.timedelta(days=1)
		while start <= end:
			date_list.append(getdate(start.date()))
			start += step

		if self.apply_type == 'Template':
			sched_map = self.get_sched_template()

		if self.assignment == "Single":
			for se in self.single_employee:
				new_shift = se.new_shift
				if self.apply_type == 'Template':
					day = datetime.datetime.strptime(str(getdate(se.target_date)), '%Y-%m-%d').strftime('%A').lower()
					new_shift = sched_map[day]['work_shift']

				employee_entry.append({
					"employee": se.employee,
					"employee_name": cstr(se.employee_name),
					"new_shift": se.new_shift,
					"target_date": getdate(se.target_date),
				})
		else:
			for d in self.employees:
				for dt in date_list:
					new_shift = d.new_shift
					if self.apply_type == 'Template':
						day = datetime.datetime.strptime(str(dt), '%Y-%m-%d').strftime('%A').lower()
						new_shift = sched_map[day]['work_shift']

					employee_entry.append({
						"employee": d.employee,
						"employee_name": cstr(d.employee_name),
						"new_shift": new_shift,
						"target_date": getdate(dt),
					})

		if employee_entry:
			for emp in employee_entry:
				shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(emp['new_shift']), as_dict=True)
				exist = frappe.db.sql("""SELECT `name` FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (emp['employee'], emp['target_date']), as_dict=True)
				if exist:
					exist = frappe.db.sql("""DELETE FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (emp['employee'], emp['target_date']), as_dict=True)
					frappe.db.commit()
				if shift:
					company = frappe.db.get_value("Employee", emp['employee'], "company")
					work_sched = frappe.new_doc("Work Schedule")
					work_sched.update({
						"employee": emp['employee'],
						"company": company,
						"target_date": emp['target_date'],
						"work_shift": shift[0]['name'],
						"shift_type": shift[0]['work_shift_type'],
						"work_hours": shift[0]['work_hours'],
						"break_mins": shift[0]['break_mins'],
						"datetime_in": self.get_date(emp['target_date'], shift[0]['time_in'], shift[0]['time_out'], shift[0]['work_shift_type'], 0), 
						"datetime_out": self.get_date(emp['target_date'], shift[0]['time_in'], shift[0]['time_out'], shift[0]['work_shift_type'], 1),
						"break_start": self.get_date(emp['target_date'], shift[0]["break_start"], shift[0]["break_end"], shift[0]['work_shift_type'], 0),
						"break_end": self.get_date(emp['target_date'], shift[0]["break_start"], shift[0]["break_end"], shift[0]['work_shift_type'], 1),
						"nd_start": self.get_date(emp['target_date'], shift[0]["nd_start"], shift[0]['time_out'], shift[0]["nd_end"], 0),
						"nd_end": self.get_date(emp['target_date'], shift[0]["nd_start"], shift[0]['time_out'], shift[0]["nd_end"], 1),
					})	
					work_sched.insert()
					if exist:
						label = "Changed Schedule " + cstr(emp['employee_name']) +""
					else:
						label = "Assigned Schedule " + cstr(emp['employee_name']) +""
						
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

	def validate_employees(self):
		date_list = []
		start = datetime.datetime.strptime(self.from_date, '%Y-%m-%d')
		end = datetime.datetime.strptime(self.to_date, '%Y-%m-%d')
		step = datetime.timedelta(days=1)
		while start <= end:
			date_list.append(getdate(start.date()))
			start += step

		unique_emp = {}
		for e in self.employees:
			if e.employee not in unique_emp:
				work_shift = e.new_shift
				if self.work_shift:
					work_shift = self.work_shift
				unique_emp[e.employee] = {
					"employee": e.employee,
					"employee_name": e.employee_name,
					"new_shift": work_shift,
				}

		employee_list = []
		if self.apply_type == 'Template':
			sched_map = self.get_sched_template()

		if len(unique_emp) == 1:
			#self.assignment = "Single"
			self.set('single_employee', [])
			for em in unique_emp:
				for dt in date_list:
					if self.apply_type == 'Template':
						day = datetime.datetime.strptime(str(dt), '%Y-%m-%d').strftime('%A').lower()
					self.append('single_employee', {
						"employee": unique_emp[em]['employee'],
						"employee_name": unique_emp[em]['employee_name'],
						"new_shift": unique_emp[em]['new_shift'],
						"target_date": dt,
					})

				employee_list.append({
					"employee": unique_emp[em]['employee'],
					"employee_name": unique_emp[em]['employee_name'],
					"new_shift": unique_emp[em]['new_shift'],
				})
		else:
			#self.assignment = "Multiple"
			
			for em in unique_emp:
				employee_list.append({
					"employee": unique_emp[em]['employee'],
					"employee_name": unique_emp[em]['employee_name'],
					"new_shift": unique_emp[em]['new_shift'],
				})

		self.set('employees', [])
		for ue in employee_list:
			row = self.append('employees', {})
			row.update(ue)

	def filter_add(self, entry):
		if not self.company:
			frappe.throw(_("Company is Required"))

		if entry == 'Company':
			employees = empget_company(self.company)
		if entry == 'Subordinates':
			employees = empget_subordinates(frappe.session.user)
		if entry == 'Employee':
			if (not self.filter_value) and (not self.filter_type):
				frappe.throw(_(" Input Filter Value and Filter Type "))
			employees = empget_employees(self.filter_type, self.filter_value, self.company)

		entries = []
		curr_emp = []
		
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

			for ent in entries:
				row = self.append('employees', ent)

		self.validate_employees()

	def clear_tables(self):
		self.set('employees', [])
		self.set('single_employee', [])

	def get_sched_template(self):
		if not self.apply_template:
			frappe.throw(_("Select Template"))

		sched_template = {}
		sched = frappe.db.sql("""SELECT * FROM `tabWork Schedule Template` WHERE `name` = %s LIMIT 1""",(self.apply_template), as_dict=1)
		days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
		if sched:
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
				}

		return sched_template

	def validate_fields(self):
		if not self.from_date or not self.to_date:
			frappe.throw(_("From Date and To Date Required"))

		if self.from_date > self.to_date:
			frappe.throw(_("From Date must be less than To Date"))

		if (self.apply_template == 'Template') and (not self.apply_template):
			frappe.throw(_("Select Template"))

	def validate_self_scheduling(self):
		self_scheduling = frappe.db.get_single_value('Timekeeping Settings', 'self_scheduling')
		if self_scheduling != 1:
			emp = frappe.db.sql(""" SELECT name, `user_id` FROM `tabEmployee` WHERE user_id = %s AND user_id != "" AND user_id is not null LIMIT 1""",( frappe.session.user ), as_dict=1)
			if emp:
				for d in self.get("employees"):
					if emp[0].name == d.employee:
						frappe.throw(_("Self Scheduling is not allowed"))

	def validate_inactive_employee(self):
		for d in self.employees:
			is_active = frappe.get_value("Employee", d.employee, "is_active")
			if not is_active:
				frappe.throw(_("Employee {0} is not active").format(d.employee))

	def create_assignment_logs(self):
		assignment_logs = frappe.new_doc("Work Schedule Assignment Logs")
		assignment_logs.update({
			"company": self.company,
			"apply_type": self.apply_type,
			"apply_template": self.apply_template,
			"from_date": self.from_date,
			"to_date": self.to_date,
			"date_assigned": getdate(nowdate()),
			"assigned_by": frappe.session.user,
			"assigned_by_name": get_user_fullname(self),
		})

		for d in self.employees:
			assignment_logs.append('employees', {
				"employee": d.employee,
				"employee_name": d.employee_name,
				"new_shift": d.new_shift,
			})

		assignment_logs.flags.ignore_permissions = True
		assignment_logs.save()

	def set_default(self):
		self_scheduling = frappe.db.get_single_value('Timekeeping Settings', 'wsa_disable_multiple')

		return self_scheduling


	def get_company(self):
		get_company = frappe.db.get_single_value('Timekeeping Settings', 'wsa_disable_company')
		
		return get_company
