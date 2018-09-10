# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import datetime
from frappe import msgprint, _
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, comma_or, get_fullname, nowdate, data, add_days
from workwise.time_keeping.timekeeping_utils import datediff_days_raw
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs, sub_date, timediff_hrs
from workwise.employee_201.emp_filters_utils import empget_employees, empget_subordinates, empget_company
from frappe.model.document import Document

class Blanket(Document):

	def validate(self):
		if self.application_type == "Leave Application":
			self.get_leave_balance()
			self.validate_days()
			self.validate_fields()
			self.validate_employee()
		elif self.application_type == "Official Business Application":
			self.get_ob_hrs()
			self.validate_employee()
		elif self.application_type == "Change Schedule Application":
			self.validate_csa_fields()
			self.csa_get_shift()

	def on_submit(self):
		if self.application_type == "Overtime Application":
			self.make_overtimes()

		elif self.application_type == "Official Business Application":
			self.make_obs()
		
		elif self.application_type == "Leave Application":
			self.make_leaves()

		elif self.application_type == "Change Schedule Application":
			self.make_change_schedule_application()


	def on_cancel(self):
		if self.application_type == "Leave Application":
			for emp in self.get("employee_table_leave"):
				frappe.db.sql("""UPDATE `tabLeave Balance` SET used_credits = used_credits - %s 
					WHERE name = %s """, (self.total_leave_days, emp.from_balance))

	#Leave Apllication
	def validate_fields(self):
		if not self.leave_type:
			frappe.throw(_("No Leave Type"))
		if not self.posting_date:
			frappe.throw(_("No Posting Date"))
		if not self.from_date:
			frappe.throw(_("No From Date"))
		if not self.to_date:
			frappe.throw(_("No To Date"))
		if not self.employee_table_leave:
			frappe.throw(_("No Employee"))

	def validate_employee(self):
		for emp in self.get("employee_table_leave"):
			location, company = frappe.get_value("Employee", emp.employee, ["location", "company"])
			if location !=  self.location:
				frappe.throw(_("Employee {0} does not belong to location {1}").format(emp.employee, self.location))
			
			if company !=  self.company:
				frappe.throw(_("Employee {0} does not belong to Company {1}").format(emp.employee, self.company))

	def get_dates(self):
		if not self.from_date:
			frappe.throw(_("No From Date"))

		if not self.to_date:
			frappe.throw(_("No To Date"))
		
		if self.from_date > self.to_date:
			frappe.throw(_("To From Date Should be Greater than To"))

		entries = [];
		dates = [];

		start = getdate(self.from_date)
		end = getdate(self.to_date)
		while start <= end:
			dates.append(start);
			start = add_days(start, 1)

		for i in dates:
			info = { 
				"leave_date": i,
				"is_holiday": self.get_holiday(i),
				"is_halfday": 0,
				"is_excluded": 0
			}

			entries.append(info);

		self.set('leave_application_table', [])
		
		for d in sorted(list(entries), key=lambda k: k['leave_date'])	:
			row = self.append('leave_application_table', {})
			row.update(d)

		self.total_leave_days = self.get_total_leave_days()

	def validate_days(self):
		self.total_leave_days = self.get_total_leave_days()

	def get_holiday(self, target_date):
		if not self.company:
			frappe.throw(_("Company is Required"))
		if not self.location:
			frappe.throw(_("Location is Required"))

		holiday_tag  = 0
		holiday = frappe.db.sql("""SELECT `name` FROM `tabHoliday` WHERE holiday_date = %s 
			AND company = %s AND location = %s """, (target_date, self.company, self.location), as_dict=True)
		if holiday:
			holiday_tag = 1

		return holiday_tag 

	def get_total_leave_days(self):
		total_leave_days = 0
		inc_holidays = frappe.get_value("Leave Type", self.leave_type, "include_holidays")

		for d in self.get('leave_application_table'):
			add_days = 1

			if d.is_half_day == 1:
				add_days = 0.5			

			if d.is_holiday == 1:
				if inc_holidays == 1:
					add_days = 1
				else:
					add_days = 0

			if d.is_excluded == 1:
				add_days = 0

			total_leave_days += add_days

		return total_leave_days

	#Working
	def get_leave_balance(self):
		for emp in self.get("employee_table_leave"):
			bal = frappe.db.sql("""SELECT `name`, credits, used_credits, from_date, to_date FROM `tabLeave Balance` WHERE employee = %s 
				AND leave_type = %s AND (%s BETWEEN from_date AND to_date) AND (%s BETWEEN from_date AND to_date) """, (emp.employee, self.leave_type, self.from_date, self.to_date), as_dict=True)

			if bal:
				emp.cur_leave_balance = flt(bal[0]['credits'], 2) - flt( bal[0]['used_credits'], 2)
				emp.from_balance = bal[0]['name']
			else:
				emp.cur_leave_balance = 0
				emp.from_balance = ""

	#Leave Applications
	def make_leaves(self):
		for d in self.get("employee_table_leave"):
			new_l_app = frappe.new_doc("Leave Application")
			new_l_app.update({
				"employee": d.employee,
				"posting_date": self.posting_date,
				"full_name": d.full_name,
				"from_date": self.from_date,
				"to_date": self.to_date,
				"leave_type": self.leave_type,
				"total_leave_days": self.total_leave_days,
				"leave_balance": d.cur_leave_balance,
				"from_balance": d.from_balance,
				"remarks": self.reason,
				"company": self.company,
				"posting_date": self.posting_date,
				"workflow_state": "Approved",
				"is_blanket": 1
			})

			for d in self.get("leave_application_table"):
				new_l_app.append('leave_application_table',{
					"leave_date": d.leave_date,
					"is_half_day": d.is_half_day,
					"is_holiday": d.is_holiday,
					"is_excluded": d.is_excluded,
				})

			new_l_app.insert()
			new_l_app.submit()

	#Overtime Applications
	def make_overtimes(self):
		total_hrs = datetimediff_hrs(self.from_datetime, self.to_datetime, "%Y-%m-%d %H:%M:%S")
		new_total_hrs = str(total_hrs)
		for d in self.get("employee_table"):
			new_ot_app = frappe.new_doc("Overtime Application")
			new_ot_app.update({
				"employee": d.employee,
				"full_name": d.full_name,
				"posting_date": self.posting_date,
				"from_date": data.format_datetime(self.from_datetime, "Y-MM-dd"),
				"to_date": data.format_datetime(self.to_datetime, "Y-MM-dd"),
				"from_time": data.format_datetime(self.from_datetime, "H:mm:ss"),
				"to_time": data.format_datetime(self.to_datetime, "H:mm:ss"),
				"total_hrs": new_total_hrs,
				"break_hrs": '0',
				"reason": self.reason,
				"company": self.company,
				"workflow_state": "Approved",
				"is_blanket": 1
			})
			new_ot_app.insert()
			new_ot_app.submit()	

	#Official Business Applications
	def get_ob_hrs(self):
		total_ob_time = 0
		for d in self.get('official_business_application_table'):
			total_hrs = 0
			if d.from_time > d.to_time:
				from_date = d.target_date+" "+d.from_time
				to_date = d.target_date+" "+d.to_time
			else:
				from_date = d.target_date+" "+d.from_time
				to_date = add_days(d.target_date, 1)+" "+d.to_time

			if not d.is_excluded == 1:
				total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")
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

			start = getdate(self.from_date)
			end = getdate(self.to_date)
			while start <= end:
				dates.append(start);
				start = add_days(start, 1)
			    
			for i in dates:
			    info = {
			        "target_date": i,
			        "from_time": "00:00:00",
			        "to_time": "00:00:00",
			        "is_holiday": self.get_holiday(i),
			        "is_excluded": 0
			    }
			    
			    official_business_application_table.append(info);
			
			entries = sorted(list(official_business_application_table), 
				key=lambda k: k['target_date'])		    

			self.set('official_business_application_table', [])
			
			for d in entries:
				row = self.append('official_business_application_table', {})
				row.update(d)

	def make_obs(self):
		for d in self.get("employee_table"):
			new_ob_app = frappe.new_doc("Official Business Application")
			new_ob_app.update({
				"employee": d.employee,
				"posting_date": self.posting_date,
				"full_name": d.full_name,
				"from_date": self.from_date,
				"to_date": self.to_date,
				"reason": self.reason,
				"company": self.company,
				"workflow_state": "Approved",
				"is_blanket": 1,
				"company_name": self.company_name,
				"contact_person": self.contact_person,
				"address": self.address,
				"total_hrs": self.total_hrs,
				"expense_items": self.expense_items,
				"expense_amount": self.expense_amount
			})

			for a in self.get("official_business_application_table"):
				new_ob_app.append('official_business_application_table',{
					"target_date": a.target_date, 
					"from_time": a.from_time,
					"to_time": a.to_time,
					"is_holiday": a.is_holiday,
					"is_excluded": a.is_excluded
				})

			new_ob_app.insert()
			new_ob_app.submit()

	#Change Schedule Application
	def validate_csa_fields(self):
		if not self.csa_date:
			frappe.throw(_("No Date"))
		if not self.get("csa_table"):
			frappe.throw(_("No Employee"))

	def csa_get_shift(self):
		fields_list = {}
		if not self.get("csa_table"):
			frappe.throw(_("No Employee"))
		for d in self.get("csa_table"):
			old_shift =  frappe.db.sql("""SELECT `name`, work_shift FROM `tabWork Schedule` WHERE employee=%s and target_date = %s LIMIT 1""",(d.employee, self.csa_date), as_dict=True);	
			for a in old_shift:
				d.current_shift = a.work_shift

	def make_change_schedule_application(self):
		for d in self.get("csa_table"):
			new_csa_app = frappe.new_doc("Change Schedule Application")
			new_csa_app.update({
				"employee": d.employee,
				"employee_name": d.employee_name,
				"target_date": self.csa_date,
				"company": self.company,
				"old_shift": d.current_shift,
				"new_shift": self.csa_newshift,
				"new_time_in": self.csa_timein,
				"new_time_out": self.csa_timeout,
				"remarks": self.csa_remarks,
				"workflow_state": "Approved",
			})

			new_csa_app.insert()
			new_csa_app.save()
			new_csa_app.submit()

	def filter_company(self):
		if self.application_type == "Change Schedule Application":
			if not self.company:
				frappe.throw(_("Company is Required"))

			entries, curr_emp = [], []
			employees = empget_company(self.company)

			for emp in employees:
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
					row = self.append('csa_table', {})
					row.update(d)

	def filter_add(self):
		if self.application_type == "Change Schedule Application":
			if not self.company:
				frappe.throw(_("Company is Required"))

			if self.filter_value and self.filter_type:
				entries, curr_emp = [], []
				employees = empget_employees(self.filter_type, self.filter_value, self.company)
				
				for emp in employees:
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
						row = self.append('csa_table', {})
						row.update(d)
			else:
				frappe.throw(_(" Input Filter Value and Filter Type "))