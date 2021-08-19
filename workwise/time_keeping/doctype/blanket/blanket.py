# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import msgprint, _
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, comma_or, get_fullname, nowdate, data, add_days, get_time, get_datetime
from workwise.time_keeping.timekeeping_utils import datediff_days_raw
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs, sub_date, timediff_hrs, chk_time_format
from workwise.employee_201.emp_filters_utils import empget_employees, empget_subordinates, empget_company
from frappe.model.document import Document

class Blanket(Document):

	def validate(self):
		if self.application_type == "Leave Application":
			self.validate_mandatory_fields()
			self.la_get_leave_balance()
			self.la_validate_days()
			self.validate_employee_company()
			self.validate_duplicate_table_entries()

		elif self.application_type == "Overtime Application":
			self.validate_mandatory_fields()
			self.ot_update_target_date()
			self.validate_employee_company()
			self.validate_duplicate_table_entries()

		elif self.application_type == "Official Business Application":
			self.validate_mandatory_fields()
			self.ob_get_ob_hrs()
			self.ob_get_target_date()
			self.validate_employee_company()
			self.validate_duplicate_table_entries()

		elif self.application_type == "Change Schedule Application":
			self.validate_mandatory_fields()
			self.csa_get_shift()
			self.validate_employee_company()
			self.validate_duplicate_table_entries()

		elif self.application_type == "Excuse Tardiness Application":
			self.validate_mandatory_fields()
			self.validate_employee_company()
			self.validate_duplicate_table_entries()

		elif self.application_type == "Undertime Application":
			self.validate_mandatory_fields()
			self.validate_employee_company()
			total_hrs = datetime.datetime.strptime(str(self.ut_to_time), '%H:%M:%S') - datetime.datetime.strptime(str(self.ut_from_time), '%H:%M:%S')
			self.ut_total_hrs = flt((total_hrs.total_seconds() / 60.0 / 60.0),2)
			self.validate_duplicate_table_entries()

		elif self.application_type == "DTR Problem Application":
			self.validate_mandatory_fields()
			self.validate_employee_company()
			self.validate_duplicate_table_entries()

		elif self.application_type == "Compensatory Time Off":
			self.validate_mandatory_fields()
			self.validate_employee_company()
			self.validate_duplicate_table_entries()

		elif self.application_type == "Timelogs Application":
			self.validate_mandatory_fields()
			self.validate_employee_company()
			self.validate_duplicate_table_entries()
			self.validate_timelogs_application()
			self.remove_tla_duplicate_entry()

	def on_submit(self):
		if self.application_type == "Leave Application":
			self.make_leave_application()

		elif self.application_type == "Overtime Application":
			self.make_overtime_application()

		elif self.application_type == "Official Business Application":
			self.make_official_business_application()

		elif self.application_type == "Change Schedule Application":
			self.make_change_schedule_application()

		elif self.application_type == "Excuse Tardiness Application":
			self.make_excuse_tardiness_application()

		elif self.application_type == "Undertime Application":
			self.make_undertime_application()

		elif self.application_type == "DTR Problem Application":
			self.make_dtr_problem_application()

		elif self.application_type == "Compensatory Time Off":
			self.make_compensatory_time_off_application()

		elif self.application_type == "Timelogs Application":
			self.make_timelogs_application()

	#def on_cancel(self):
	#	if self.application_type == "Leave Application":
	#		for emp in self.get("blad_table"):
	#			frappe.db.sql("""UPDATE `tabLeave Balance` SET used_credits = used_credits - %s 
	#				WHERE name = %s """, (self.la_total_leave_days, emp.from_balance))

	#Filter
	def filter_reset(self):
		if self.application_type == "Leave Application":
			self.set('blad_table', [])
		if self.application_type == "Change Schedule Application":
			self.set('bcsa_table', [])
		if self.application_type == "Compensatory Time Off":
			self.set('bctod_table', [])
		else:
			self.set('bad_table', [])
	
	def filter_add(self):
		if not self.company:
			frappe.throw(_("Company is Required"))

		if self.filter_value and self.filter_type:
			entries = []
			curr_emp = []
			employees = empget_employees(self.filter_type, self.filter_value, self.company)
			
			if self.application_type == "Leave Application":
				if self.get("blad_table"):
					for emp in self.get("blad_table"):
						curr_emp.append(emp.employee)

				if employees:
					for d in employees:
						if d.name not in curr_emp:
							row = {
								"employee": d.name,
								"full_name": d.full_name,
							}
							entries.append(row)

					for d in entries:
						row = self.append('blad_table', {})
						row.update(d)

			elif self.application_type == "Change Schedule Application":
				if self.get("bcsa_table"):
					for emp in self.get("bcsa_table"):
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
						row = self.append('bcsa_table', {})
						row.update(d)

			elif self.application_type == "Compensatory Time Off":
				if self.get("bctod_table"):
					for emp in self.get("bctod_table"):
						curr_emp.append(emp.employee)

				if employees:
					for d in employees:
						if d.name not in curr_emp:
							row = {
								"employee": d.name,
								"full_name": d.full_name,
							}
							entries.append(row)

					for d in entries:
						row = self.append('bctod_table', {})
						row.update(d)
			else:
				if self.get("bad_table"):
					for emp in self.get("bad_table"):
						curr_emp.append(emp.employee)

				if employees:
					for d in employees:
						if d.name not in curr_emp:
							row = {
								"employee": d.name,
								"full_name": d.full_name,
							}
							entries.append(row)

					for d in entries:
						row = self.append('bad_table', {})
						row.update(d)
		else:
			frappe.throw(_(" Input Filter Value and Filter Type "))

	def filter_subordinates(self):
		entries = []
		curr_emp = []
		employees = empget_subordinates(frappe.session.user)

		if self.application_type == "Leave Application":
			if self.get("blad_table"):
				for emp in self.get("blad_table"):
					curr_emp.append(emp.employee)

			if employees:
				for d in employees:
					if d.name not in curr_emp:
						row = {
							"employee": d.name,
							"full_name": d.full_name,
						}
						entries.append(row)

				for d in entries:
					row = self.append('blad_table', {})
					row.update(d)

		elif self.application_type == "Change Schedule Application":
			if self.get("bcsa_table"):
				for emp in self.get("bcsa_table"):
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
					row = self.append('bcsa_table', {})
					row.update(d)

		elif self.application_type == "Compensatory Time Off":
			if self.get("bctod_table"):
				for emp in self.get("bctod_table"):
					curr_emp.append(emp.employee)

			if employees:
				for d in employees:
					if d.name not in curr_emp:
						row = {
							"employee": d.name,
							"full_name": d.full_name,
						}
						entries.append(row)

				for d in entries:
					row = self.append('bctod_table', {})
					row.update(d)
		else:
			if self.get("bad_table"):
				for emp in self.get("bad_table"):
					curr_emp.append(emp.employee)

			if employees:
				for d in employees:
					if d.name not in curr_emp:
						row = {
							"employee": d.name,
							"full_name": d.full_name,
						}
						entries.append(row)

				for d in entries:
					row = self.append('bad_table', {})
					row.update(d)

	#General Use
	def validate_mandatory_fields(self):
		if not self.company:
			frappe.throw(_("Company is Required"))
		if not self.posting_date:
			frappe.throw(_("Posting Date is Required"))

		if self.application_type == "Leave Application":
			if not self.la_leave_type:
				frappe.throw(_("No Leave Type"))
			if not self.posting_date:
				frappe.throw(_("No Posting Date"))
			if not self.la_from_date:
				frappe.throw(_("No From Date"))
			if not self.la_to_date:
				frappe.throw(_("No To Date"))
			if not self.la_remarks:
				frappe.throw(_("No Reason"))
			if not self.blad_table:
				frappe.throw(_("No Employee"))

		elif self.application_type == "Overtime Application":
			if not self.ot_from_date:
				frappe.throw(_("No From Date"))
			if not self.ot_to_date:
				frappe.throw(_("No To Date"))
			if not self.ot_total_hrs:
				frappe.throw(_("No Total Hours"))
			if not self.ot_from_time:
				frappe.throw(_("No From Time"))
			if not self.ot_to_time:
				frappe.throw(_("No To Time"))
			if not self.ot_reason:
				frappe.throw(_("No Reason"))
			if not self.bad_table:
				frappe.throw(_("No Employee"))

		elif self.application_type == "Official Business Application":
			if not self.ob_reason:
				frappe.throw(_("No Reason"))
			if not self.ob_from_date:
				frappe.throw(_("No From Date"))
			if not self.ob_to_date:
				frappe.throw(_("No To Date"))
			if not self.ob_address:
				frappe.throw(_("No Address"))
			if not self.ob_contact_person:
				frappe.throw(_("No Contact Person"))
			if not self.bad_table:
				frappe.throw(_("No Employee"))

		elif self.application_type == "Change Schedule Application":
			if not self.csa_target_date:
				frappe.throw(_("No Date"))
			if not self.csa_new_shift:
				frappe.throw(_("No New Shift"))
			if not self.bcsa_table:
				frappe.throw(_("No Employee"))

		elif self.application_type == "Excuse Tardiness Application":
			if not self.eta_date:
				frappe.throw(_("No Date"))
			if not self.eta_from_time:
				frappe.throw(_("No From Time"))
			if not self.eta_type:
				frappe.throw(_("No Type"))
			if not self.eta_to_time:
				frappe.throw(_("No To Time"))
			if not self.bad_table:
				frappe.throw(_("No Employee"))

		elif self.application_type == "Undertime Application":
			if not self.ut_from_date:
				frappe.throw(_("No Date"))
			if not self.ut_from_time:
				frappe.throw(_("No From Time"))
			if not self.ut_to_time:
				frappe.throw(_("No To Time"))
			if not self.bad_table:
				frappe.throw(_("No Employee"))

		elif self.application_type == "DTR Problem Application":
			if not self.dtr_target_date:
				frappe.throw(_("No Date"))
			if not self.time_record_request:
				frappe.throw(_("No Entries Time Record Request Table"))
			if not self.bad_table:
				frappe.throw(_("No Employee"))

		elif self.application_type == "Compensatory Time Off":
			if not self.cto_type:
				frappe.throw(_("No Type"))
			if not self.bctod_table:
				frappe.throw(_("No Employee"))

		elif self.application_type == "Timelogs Application":
			if not self.bad_table:
				frappe.throw(_("No Employee(s)"))
			if not self.timelogs_application_table:
				frappe.throw(_("No Details Entered"))

	def validate_employee_company(self):
		if self.application_type == "Leave Application":
			for emp in self.get("blad_table"):
				location, company = frappe.get_value("Employee", emp.employee, ["location", "company"])

				if self.location:
					if location !=  self.location:
						frappe.throw(_("Employee {0} does not belong to location {1}").format(emp.employee, self.location))
				
				if self.company:
					if company !=  self.company:
						frappe.throw(_("Employee {0} does not belong to Company {1}").format(emp.employee, self.company))

		if self.application_type == "Change Schedule Application":
			for emp in self.get("bcsa_table"):
				company = frappe.get_value("Employee", emp.employee, "company")
				
				if self.company:
					if company !=  self.company:
						frappe.throw(_("Employee {0} does not belong to Company {1}").format(emp.employee, self.company))

		else:
			for emp in self.get("bad_table"):
				company = frappe.get_value("Employee", emp.employee, "company")
				
				if self.company:
					if company !=  self.company:
						frappe.throw(_("Employee {0} does not belong to Company {1}").format(emp.employee, self.company))

	def validate_duplicate_table_entries(self):
		unique_emp = []
		unique_entries = []

		if self.application_type == "Leave Application":
			for d in self.blad_table:
				if d.employee not in unique_emp:
					unique_emp.append(d.employee);

					i = {
						"employee": d.employee,
						"full_name": d.full_name,
						"cur_leave_balance": d.cur_leave_balance,
						"from_balance": d.from_balance
					}	
					unique_entries.append(i);

				self.set('blad_table', [])
				for ue in unique_entries:
					row = self.append('blad_table', {})
					row.update(ue)

		if self.application_type == "Change Schedule Application":
			for d in self.bcsa_table:
				if d.employee not in unique_emp:
					unique_emp.append(d.employee);

					i = {
						"employee": d.employee,
						"employee_name": d.employee_name,
						"current_shift": d.current_shift
					}	
					unique_entries.append(i);

				self.set('bcsa_table', [])
				for ue in unique_entries:
					row = self.append('bcsa_table', {})
					row.update(ue)

		if self.application_type == "Compensatory Time Off":
			for d in self.bctod_table:
				if d.employee not in unique_emp:
					unique_emp.append(d.employee);

					i = {
						"employee": d.employee,
						"full_name": d.full_name,
						"credit_balance": d.credit_balance
					}	
					unique_entries.append(i);

				self.set('bctod_table', [])
				for ue in unique_entries:
					row = self.append('bctod_table', {})
					row.update(ue)

		else:
			for d in self.bad_table:
				if d.employee not in unique_emp:
					unique_emp.append(d.employee);

					i = {
						"employee": d.employee,
						"full_name": d.full_name
					}	
					unique_entries.append(i);

				self.set('bad_table', [])
				for ue in unique_entries:
					row = self.append('bad_table', {})
					row.update(ue)

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

	def get_recipients(self, employee):
		managers_list = ""
		recipients = []
		managers = frappe.db.sql("""SELECT ES.employee, E.user_id FROM `tabEmployee Subordinates` ES 
			INNER JOIN `tabSubordinates` S ON S.parent = ES.name
			LEFT JOIN `tabEmployee` E ON ES.employee = E.name
			WHERE S.subordinate = %s """,(employee), as_dict=True)
		for d in managers:
			if d.user_id:
				recipients.append(d.user_id)

		if recipients:
			send_to = ', '.join(str(x) for x in recipients)
			managers_list = send_to

		return managers_list

	#Leave Apllication Processes
	def la_get_dates(self):
		if not self.la_from_date:
			frappe.throw(_("No From Date"))

		if not self.la_to_date:
			frappe.throw(_("No To Date"))
		
		if self.la_from_date > self.la_to_date:
			frappe.throw(_("To From Date Should be Greater than To"))

		entries = [];
		dates = [];

		start = getdate(self.la_from_date)
		end = getdate(self.la_to_date)
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

		self.la_total_leave_days = self.la_get_total_leave_days()

	def la_validate_days(self):
		self.la_total_leave_days = self.la_get_total_leave_days()

	def la_get_total_leave_days(self):
		total_leave_days = 0
		inc_holidays = frappe.get_value("Leave Type", self.la_leave_type, "include_holidays")

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
			
			if d.is_second_half == 1:
				d.is_half_day = 1
				add_days = 0.5

			if getdate(d.leave_date).weekday() == 5:
				lvbal_saturday = frappe.db.get_single_value('Timekeeping Settings', 'lvbal_saturday')
				if lvbal_saturday > 0:
					add_days = flt(lvbal_saturday, 8)

			total_leave_days += add_days

		return total_leave_days

	def la_get_leave_balance(self):
		for emp in self.get("blad_table"):

			valid_entry = {}
			less_entry = {}
			from_balance = ""
			add, less, total_balance = 0, 0, 0
			min_date = None
			deduct_to = frappe.get_value("Leave Type", self.la_leave_type, "deduct_to")
			if not deduct_to:
				deduct_to = self.la_leave_type
			lb_entries = frappe.db.sql(""" SELECT * FROM `tabLB Entry` WHERE `employee` = %s AND 
				(`leave_type` = %s OR `deduct_credits_to` = %s) AND `company` = %s ORDER BY `from_date` 
				ASC """, (emp.employee, deduct_to, deduct_to, self.company), as_dict=1)
			
			for d in lb_entries:
				if d.balance_type == "Add":
					if deduct_to == d.leave_type:
						if d.name not in valid_entry:
							valid_entry[d.name] = {
								"credits": d.credits,
								"from": getdate(d.from_date),
								"to": getdate(d.to_date),
								"used": 0,
							}
				else:
					if d.deduct_credits_to == deduct_to:
						if d.name not in less_entry:
							less_entry[d.name] = {
								"used": 0,
								"credits": d.credits,
								"from": getdate(d.from_date),
								"to": getdate(d.to_date),
							}
			have_lbentry = 0
			for vl in valid_entry:
				for le in less_entry:
					to_less = 0
					if valid_entry[vl]['credits'] > 0 and not less_entry[le]['used']:
						if ( valid_entry[vl]['from'] <= less_entry[le]['from'] <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= less_entry[le]['to'] <= valid_entry[vl]['to'] ):
							if less_entry[le]['credits'] > valid_entry[vl]['credits']:
								to_less += valid_entry[vl]['credits']
								less_entry[le]['credits'] -= valid_entry[vl]['credits']
							else:
								to_less += less_entry[le]['credits']
								less_entry[le]['used'] = 1
						valid_entry[vl]['credits'] -= to_less
				if getdate(valid_entry[vl]['from']) <= getdate(self.la_from_date) and getdate(valid_entry[vl]['to']) >= getdate(self.la_to_date) and valid_entry[vl]['credits'] > 0:
					if total_balance < self.la_total_leave_days:
						from_balance += cstr(vl)
					total_balance += valid_entry[vl]['credits']
					valid_entry[vl]['used'] = 1
					have_lbentry = 1
					
			if have_lbentry == 1:
				for vl in valid_entry:
					if valid_entry[vl]['used'] == 0 and valid_entry[vl]['credits'] > 0:
						if ( valid_entry[vl]['from'] <= getdate(self.la_from_date) <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= getdate(self.la_from_date) <= valid_entry[vl]['to'] )\
						or ( getdate(self.la_from_date) <= valid_entry[vl]['from'] <= getdate(self.la_to_date) ) or ( getdate(self.la_from_date) <= valid_entry[vl]['to'] <= getdate(self.la_to_date) ):
							if total_balance < self.la_total_leave_days:
								from_balance += cstr(vl)
							total_balance += valid_entry[vl]['credits']
							valid_entry[vl]['used'] = 1
			if total_balance > 0 :
				emp.cur_leave_balance = total_balance
				emp.from_balance = from_balance
			else:
				emp.cur_leave_balance = 0
				emp.from_balance = ""

	#Make Leave Application(s)
	def make_leave_application(self):
		for d in self.get("blad_table"):
			leave_application = frappe.new_doc("Leave Application")
			leave_application.update({
				"employee": d.employee,
				"full_name": d.full_name,
				"leave_type": self.la_leave_type,
				"total_leave_days": self.la_total_leave_days,
				"leave_balance": d.cur_leave_balance,
				"posting_date": self.posting_date,
				"from_date": self.la_from_date,
				"to_date": self.la_to_date,
				"remarks": self.la_remarks,
				"approved_on": nowdate(),
				"workflow_state": "Approved",
				"is_lwop": self.la_is_lwop,
				"is_blanket": 1,
				"approved_by": frappe.session.user,
				"from_balance": d.from_balance,
				"company": self.company,
				"owner": frappe.session.user,
				"managers_list": self.get_recipients(d.employee),
			})

			for d in self.get("leave_application_table"):
				leave_application.append('leave_application_table',{
					"leave_date": d.leave_date,
					"is_half_day": d.is_half_day,
					"is_second_half": d.is_second_half,
					"is_holiday": d.is_holiday,
					"is_excluded": d.is_excluded,
				})

			leave_application.insert()
			leave_application.save()
			leave_application.submit()

	#Overtime Application
	def ot_calculate_totals(self):	
		self.total_hrs = 0
		from_date = str(self.ot_from_date) + ' ' + str(self.ot_from_time)
		to_date = str(self.ot_to_date) + ' ' + str(self.ot_to_time)
		
		if from_date <= to_date:
			total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")
			self.ot_total_hrs = total_hrs - flt(self.ot_break_hrs, 8)
		else:
			if self.ot_break_hrs:
				total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")
				self.ot_total_hrs = total_hrs - flt(self.ot_break_hrs, 8)
			else:
				total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")
				self.ot_total_hrs = total_hrs

	def ot_validate_time_format(self):
		time_fds = ['from_time', 'to_time']
		for fd in time_fds:
			chk_time_format(str(self.get(fd)), "%H:%M:%S")

	def ot_update_target_date(self):
		target_date = datetime.datetime.strptime(str(self.ot_from_date) + ' ' + str(self.ot_from_time), '%Y-%m-%d %H:%M:%S').date()

		if self.ot_is_previous:
			self.ot_target_date = target_date - datetime.timedelta(days=1)
		else:
			self.ot_target_date = target_date

	#Make Overtime Application(s)
	def make_overtime_application(self):
		for d in self.get("bad_table"):
			new_ot_app = frappe.new_doc("Overtime Application")
			new_ot_app.update({
				"employee": d.employee,
				"full_name": d.full_name,
				"is_previous": self.ot_is_previous,
				"target_date": self.ot_target_date,
				"posting_date": self.posting_date,
				"company": self.company,
				"from_date": self.ot_from_date,
				"to_date": self.ot_to_date,
				"total_hrs": self.ot_total_hrs,
				"from_time": self.ot_from_time,
				"to_time": self.ot_to_time,
				"break_hrs": self.ot_break_hrs,
				"reason": self.ot_reason,
				"approved_on": nowdate(),
				"workflow_state": "Approved",
				"is_blanket": 1,
				"approved_by": frappe.session.user,
				"owner": frappe.session.user,
				"managers_list": self.get_recipients(d.employee),
			})
			new_ot_app.insert()
			new_ot_app.save()
			new_ot_app.submit()

	#Official Business Application
	def ob_get_ob_dates(self):
		total_balance = 0
		self.set('official_business_application_table', [])
		if not self.ob_from_date:
			frappe.throw(_("No From Date"))

		if not self.ob_to_date:
			frappe.throw(_("No To Date"))
		
		if self.ob_from_date > self.ob_to_date:
			frappe.throw(_("To From Date Should be Greater than To"))
			
		else:
			entries = [];
			dates = [];
			official_business_application_table = [];

			start = datetime.datetime.strptime(str(self.ob_from_date), '%Y-%m-%d')
			end = datetime.datetime.strptime(str(self.ob_to_date), '%Y-%m-%d')
			step = datetime.timedelta(days=1)
			
			while start <= end:
			    dates.append(start.date());
			    start += step
			    
			for i in dates:
			    info = {
				    "target_date": i,
			        "date": i,
			        "to_date": i,
			        "from_time": "00:00:00",
			        "to_time": "00:00:00",
			        "is_holiday": self.get_holiday(i),
			        "is_excluded": 0,
			        "is_previous": 0
			    }
			    
			    official_business_application_table.append(info);
			
			entries = sorted(list(official_business_application_table), 
				key=lambda k: k['target_date'])		    

			self.set('official_business_application_table', [])
			
			for d in entries:
				row = self.append('official_business_application_table', {})
				row.update(d)

	def ob_get_ob_hrs(self):
		total_ob_time = 0
		for d in self.get('official_business_application_table'):
			total_hrs = 0
			from_date = get_datetime(str(d.date)+" "+str(d.from_time))
			to_date = get_datetime(str(d.to_date)+" "+str(d.to_time))
				
			if not d.is_excluded == 1:
				total_hrs = abs(((from_date - to_date).total_seconds()) / 60 /60)
				total_ob_time += total_hrs
				d.hrs = total_hrs

		self.ob_total_hrs = total_ob_time

	def ob_change_time(self):
		for d in self.get('official_business_application_table'):
			d.from_time = self.ob_from_time
			d.to_time = self.ob_to_time

	def ob_get_target_date(self):
		for d in self.get('official_business_application_table'):
			if d.is_previous == 1:
				d.target_date = getdate(d.date) - datetime.timedelta(days=1)
			else:
				d.target_date = d.date

	#Make Official Business Application(s)
	def make_official_business_application(self):
		for d in self.get("bad_table"):
			new_ob_app = frappe.new_doc("Official Business Application")
			new_ob_app.update({
				"employee": d.employee,
				"full_name": d.full_name,
				"company_name": self.ob_company_name,
				"posting_date": self.posting_date,
				"reason": self.ob_reason,
				"from_date": self.ob_from_date,
				"from_time": self.ob_from_time,
				"to_date": self.ob_to_date,
				"to_time": self.ob_to_time,
				"total_hrs": self.ob_total_hrs,
				"attachment": self.ob_attachment,
				"expense_items": self.ob_expense_items,
				"expense_amount": self.ob_expense_amount,
				"address": self.ob_address,
				"contact_person": self.ob_contact_person,
				"company": self.company,
				"approved_on": nowdate(),
				"workflow_state": "Approved",
				"is_blanket": 1,
				"approved_by": frappe.session.user,
				"owner": frappe.session.user,
				"managers_list": self.get_recipients(d.employee),
			})

			for a in self.get("official_business_application_table"):
				new_ob_app.append('official_business_application_table',{
				    "target_date": a.target_date, 
			        "date": a.date,
			        "to_date": a.to_date,
					"from_time": a.from_time,
					"to_time": a.to_time,
					"is_holiday": a.is_holiday,
					"is_excluded": a.is_excluded,
					"is_previous": a.is_previous
				})

			new_ob_app.insert()
			new_ob_app.save()
			new_ob_app.submit()

	#Change Schedule Application
	def csa_get_shift(self):
		fields_list = {}
		if not self.get("bcsa_table"):
			frappe.throw(_("No Employee"))
		for d in self.get("bcsa_table"):
			old_shift =  frappe.db.sql("""SELECT `name`, work_shift FROM `tabWork Schedule` WHERE employee=%s and target_date = %s LIMIT 1""",(d.employee, self.csa_target_date), as_dict=True);	
			for a in old_shift:
				d.current_shift = a.work_shift

	#Make Change Schedule Application(s)
	def make_change_schedule_application(self):
		for d in self.get("bcsa_table"):
			new_csa_app = frappe.new_doc("Change Schedule Application")
			new_csa_app.update({
				"target_date": self.csa_target_date,
				"employee": d.employee,
				"employee_name": d.employee_name,
				"company": self.company,
				"posting_date": self.posting_date,
				"old_shift": d.current_shift,
				"new_shift": self.csa_new_shift,
				"new_time_in": self.csa_new_time_in,
				"new_time_out": self.csa_new_time_out,
				"remarks": self.csa_remarks,
				"approved_on": nowdate(),
				"workflow_state": "Approved",
				"is_blanket": 1,
				"approved_by": frappe.session.user,
				"owner": frappe.session.user,
				"managers_list": self.get_recipients(d.employee),
			})

			new_csa_app.insert()
			new_csa_app.save()
			new_csa_app.submit()

	#Excuse Tardiness Application
	def eta_load_timecard(self):
		for emp in self.get("bad_table"):
			bio_id = ""
			bio_id = frappe.get_value("Employee", emp.employee, "biometrics_id")
			if bio_id:
				time_in = frappe.db.sql(""" SELECT `time` FROM `tabTime Card` WHERE `biometrics_id` = %s AND `card_type` = 1 AND `is_disabled` = 0 AND `date` = %s LIMIT 1 """, (bio_id, self.eta_date), as_dict=True)
				if time_in:
					self.eta_to_time = time_in[0].time
				time_out = frappe.db.sql(""" SELECT `time` FROM `tabTime Card` WHERE `biometrics_id` = %s AND `card_type` = 0 AND `is_disabled` = 0 AND `date` = %s LIMIT 1 """, (bio_id, self.eta_date), as_dict=True)
				if time_out:
					self.eta_from_time = time_out[0].time

	#Make Excuse Tardiness Application(s)
	def make_excuse_tardiness_application(self):
		for d in self.get("bad_table"):
			new_et_app = frappe.new_doc("Excuse Tardiness Application")
			new_et_app.update({
				"employee": d.employee,
				"employee_name": d.full_name,
				"posting_date": self.posting_date,
				"company": self.company,
				"date": self.eta_date,
				"from_time": self.eta_from_time,
				"type": self.eta_type,
				"to_time": self.eta_to_time,
				"reason": self.eta_reason,
				"attachment": self.eta_attachment,
				"approved_on": nowdate(),
				"workflow_state": "Approved",
				"is_blanket": 1,
				"approved_by": frappe.session.user,
				"owner": frappe.session.user,
				"managers_list": self.get_recipients(d.employee),
			})

			new_et_app.insert()
			new_et_app.save()
			new_et_app.submit()

	#Make Undertime Application(s)
	def make_undertime_application(self):
		for d in self.get("bad_table"):
			new_ut_app = frappe.new_doc("Undertime Application")
			new_ut_app.update({
				"employee": d.employee,
				"employee_name": d.full_name,
				"posting_date": self.posting_date,
				"company": self.company,
				"from_date": self.ut_from_date,
				"from_time": self.ut_from_time,
				"to_time": self.ut_to_time,
				"total_hrs": self.ut_total_hrs,
				"reason": self.ut_reason,
				"attachment": self.ut_attachment,
				"approved_on": nowdate(),
				"workflow_state": "Approved",
				"is_blanket": 1,
				"approved_by": frappe.session.user,
				"owner": frappe.session.user,
				"managers_list": self.get_recipients(d.employee),
			})

			new_ut_app.insert()
			new_ut_app.save()
			new_ut_app.submit()

	#DTR Problem Application
	def dtr_get_card_type(self, req):
		if req.type == "Time In":
			card_type = 0
		if req.type == "Time Out":
			card_type = 1
		if req.type == "Break In":
			card_type = 2
		if req.type == "Break Out":
			card_type = 3
			
		return card_type

	#def dtr_get_timecard(self, card, emp):
	#	timecard_sel = frappe.db.sql("""SELECT TC.`name`, TC.`date`, TC.`time` FROM `tabTime Card` TC JOIN `tabEmployee` TE WHERE TC.biometrics_id = TE.biometrics_id  AND TC.`date` = %s AND TC.`card_type` = %s AND TE.`name` = %s LIMIT 1 """, (self.dtr_target_date, card, emp), as_dict=True)
	#	return timecard_sel

	#Make DTR Problem Application(s)
	def make_dtr_problem_application(self):
		#frappe.throw(_('req.type'))
		timecard_info = {}
		for d in self.get("bad_table"):
			new_dtr_app = frappe.new_doc("DTR Problem Application")
			new_dtr_app.update({
				"employee": d.employee,
				"employee_name": d.full_name,
				"posting_date": self.posting_date,
				"company": self.company,
				"target_date": self.dtr_target_date,
				"reason": self.dtr_reason,
				"attachment": self.dtr_attachment,
				"approved_on": nowdate(),
				"workflow_state": "Approved",
				"is_blanket": 1,
				"approved_by": frappe.session.user,
				"owner": frappe.session.user,
				"managers_list": self.get_recipients(d.employee),
			})

			for req in self.time_record_request:
				card = self.dtr_get_card_type(req)
				#timecard_sel = self.dtr_get_timecard(card, d.employee)
				#current = ""
				#time_card = ""
				#for a in timecard_sel:
				#	current = a.time
				#	time_card = a.name
				timecard_info = {
					"type": req.type,
					"card_type": card,
					"request": req.request,
				}
				new_dtr_app.append('time_record_request', timecard_info)

			new_dtr_app.insert()
			new_dtr_app.save()
			new_dtr_app.submit()

	#Compensatory Time Off
	def cto_validate_file_cto(self):
		from_date = datetime.datetime.strptime(str(self.cto_date) + ' ' + str(self.cto_from_time), '%Y-%m-%d %H:%M:%S')
		to_date = datetime.datetime.strptime(str(self.cto_date) + ' ' + str(self.cto_to_time), '%Y-%m-%d %H:%M:%S')
		if from_date <= to_date:
			total_hrs = to_date - from_date
		else:
			total_hrs = to_date - from_date + datetime.timedelta(days=1)
		self.cto_total_hours = abs(flt(total_hrs.total_seconds() /60 /60, 2))
		self.cto_credits_earned = flt(self.cto_total_hours,2)/8
		if self.cto_credits_earned > 1:
			self.cto_credits_earned = 1.0

		self.cto_balance = flt(self.cto_credits_earned,2) - flt(self.cto_credits_used,2)

	def cto_validate_use_cto(self, d):
		total_hrs =  datetime.datetime.strptime(str(self.cto_use_totime), '%H:%M:%S') -  datetime.datetime.strptime(str(self.cto_use_fromtime), '%H:%M:%S')
		total_hours = flt((total_hrs.total_seconds() / 60.0 / 60.0),2)
		self.cto_required_credits = flt(total_hours,2)/8
		if self.cto_required_credits > 1:
			self.cto_required_credits = 1.0

		total_credits_earned = 0.00
		last_date = ""
		date_list = []
		current_credits = frappe.db.sql("""SELECT credits_earned - credits_used as cred_balance, `date` FROM `tabCompensatory Time Off` WHERE `type` = "File" AND `employee` = %s AND `docstatus` = 1 ORDER BY `date` DESC""",( d.employee ), as_dict=1)

		if current_credits:
			for a in current_credits:
				total_credits_earned += flt(a.cred_balance, 2)
				date_list.append(a.date)

			last_date = date_list[-1]

		d.credit_balance = total_credits_earned
			
		return last_date

	def cto_validate_date_use_cto(self):
		for d in self.get("bctod_table"):
			last_date = self.cto_validate_use_cto(d)
			if getdate(self.cto_use_date) < getdate(last_date):
				frappe.throw(_("Employee {2} Cannot Use CTO Application for date {0} because last Filed CTO Application date is {1}").format( self.cto_use_date, last_date, d.employee ))

	#Make Compensatory Time Off(s)
	def make_compensatory_time_off_application(self):
		req_credits = flt(self.cto_required_credits, 2)

		for d in self.get("bctod_table"):
			new_cto = frappe.new_doc("Compensatory Time Off")

			if self.cto_type == "File":
				new_cto.update({
					"employee": d.employee,
					"employee_name": d.full_name,
					"posting_date": self.posting_date,
					"company": self.company,
					"type": self.cto_type,
					"date": self.cto_date,
					"credits_earned": self.cto_credits_earned,
					"credits_used": self.cto_credits_used,
					"balance": self.cto_balance,
					"from_time": self.cto_from_time,
					"to_time": self.cto_to_time,
					"total_hours": self.cto_total_hours,
					"reason": self.cto_reason,
					"approved_on": nowdate(),
					"workflow_state": "Approved",
					"is_blanket": 1,
					"approved_by": frappe.session.user,
					"owner": frappe.session.user,
					"managers_list": self.get_recipients(d.employee),
				})

			if self.cto_type == "Use":
				if req_credits > d.credit_balance:
					frappe.throw(_("Not enough credits for Employee {0}").format(d.employee))
				else:
					new_cto.update({
						"employee": d.employee,
						"employee_name": d.full_name,
						"posting_date": self.posting_date,
						"company": self.company,
						"type": self.cto_type,
						"use_date": self.cto_use_date,
						"total_credits_earned": d.credit_balance,
						"use_fromtime": self.cto_use_fromtime,
						"use_totime": self.cto_use_totime,
						"required_credits": self.cto_required_credits,
						"use_reason": self.cto_use_reason,
						"approved_on": nowdate(),
						"workflow_state": "Approved",
						"is_blanket": 1,
						"approved_by": frappe.session.user,
						"owner": frappe.session.user,
						"managers_list": self.get_recipients(d.employee),
				})

			new_cto.insert()
			new_cto.save()
			new_cto.submit()

	def make_timelogs_application(self):
		for d in self.get("bad_table"):
			new_tla_app = frappe.new_doc("Timelogs Application")
			new_tla_app.update({
				"employee": d.employee,
				"employee_name": d.full_name,
				"posting_date": self.posting_date,
				"company": self.company,
				"location": self.timelogs_application_location,
				"reason": self.dtr_reason,
				"from_date": self.tla_fromdate,
				"to_date": self.tla_todate,
				"cost_center": self.timelogs_application_cost_center,
				"approved_on": nowdate(),
				"workflow_state": "Approved",
				"is_blanket": 1,
				"approved_by": frappe.session.user,
				"owner": frappe.session.user,
				"managers_list": self.get_recipients(d.employee),
			})

			for req in self.timelogs_application_table:
				row = {
					"target_date": req.target_date,
					"type": req.type,
					"request": req.request,
					"location": req.location,
					"cost_center": req.cost_center,
				}
				new_tla_app.append('timelogs', row)

			new_tla_app.insert()
			new_tla_app.save()
			new_tla_app.submit()

	def tla_fill_location_cost_center(self):
		if self.get("timelogs_application_table"):
			for t in self.timelogs_application_table:
				t.location =  self.timelogs_application_location
				t.cost_center = self.timelogs_application_cost_center

	def validate_timelogs_application(self):
		for d in self.bad_table:
			location_list = []
			cost_center_list = []

			bio_id = frappe.get_value('Employee', d.employee, 'biometrics_id')
			if not bio_id:
				frappe.throw(_("<b>Timelogs Application: {0}</b><hr> Employee {1} has no Biometrics ID").format(d.employee, d.employee_name))

			location = frappe.db.sql("""SELECT `name` FROM `tabLocation` WHERE `company` = %s """, (self.company), as_dict=True)
			for loc in location:
				location_list.append(loc.name)

			cost_center = frappe.db.sql("""SELECT `name` FROM `tabCost Center` WHERE `company` = %s """, (self.company), as_dict=True)
			for cos in cost_center:
				cost_center_list.append(cos.name)

			if self.timelogs_application_location and self.timelogs_application_location not in location_list:
				frappe.throw(_( "Invalid Location: "+str(self.timelogs_application_location) ))
			if self.timelogs_application_cost_center and self.timelogs_application_cost_center not in cost_center_list:
				frappe.throw(_( "Invalid Cost Center: "+str(self.timelogs_application_cost_center) ))
			for t in self.timelogs_application_table:
				if t.location and t.location not in location_list:	
					frappe.throw(_( "Invalid Location: "+str(t.location) ))
				if t.location and t.location not in location_list:
					frappe.throw(_( "Invalid Cost Center: "+str(t.cost_center) ))

				#Get Current Time Card
				if t.type == "Time In":
					card_type = 0
				if t.type == "Time Out":
					card_type = 1
				if t.type == "Break In":
					card_type = 2
				if t.type == "Break Out":
					card_type = 3

				current = frappe.db.sql("""SELECT TC.`name`, TC.`time` FROM `tabTime Card` TC INNER JOIN `tabEmployee` TE ON TC.biometrics_id = TE.biometrics_id
					WHERE TC.`date` = %s AND TC.`card_type` = %s AND TE.`name` = %s LIMIT 1 """, (getdate(t.target_date), card_type, d.employee), as_dict=True)
				if current:
					t.current = current[0].time
				else:
					t.current = None

				if not t.location:
					t.location = self.timelogs_application_location
				if not t.cost_center:
					t.cost_center = self.timelogs_application_cost_center

	def remove_tla_duplicate_entry(self):
		unique_ent = []
		unique_entries = []
		for req in self.timelogs_application_table:
			if str(req.target_date)+str(req.type) not in unique_ent:
				unique_ent.append(str(req.target_date)+str(req.type));

				i = {
					"target_date": req.target_date,
					"type": req.type,
					"request": req.request,
					"location": req.location,
					"cost_center": req.cost_center,
				}	
				unique_entries.append(i);

		self.set('timelogs_application_table', [])
		for ue in unique_entries:
			row = self.append('timelogs_application_table', {})
			row.update(ue)

	def daterange(self, start_date, end_date):
		for n in range( int((end_date - start_date).days) + 1):
			yield start_date + datetime.timedelta(n)

	def tla_populate_dates(self):
		if getdate(self.tla_fromdate) > getdate(self.tla_todate):
			self.set('timelogs_application_table', [])

		if self.tla_fromdate and self.tla_todate and getdate(self.tla_fromdate) <= getdate(self.tla_todate):
			entries = []
			for target_date in self.daterange(getdate(self.tla_fromdate), getdate(self.tla_todate)):
				i = {
					"target_date": getdate(target_date),
					"type": "Time In",
					"location":  self.timelogs_application_location,
					"cost_center": self.timelogs_application_cost_center,
				}
				entries.append(i);
				i = {
					"target_date": getdate(target_date),
					"type": "Time Out",
					"location":  self.timelogs_application_location,
					"cost_center": self.timelogs_application_cost_center,
				}
				entries.append(i);

			self.set('timelogs_application_table', [])
			for ue in entries:
				row = self.append('timelogs_application_table', {})
				row.update(ue)