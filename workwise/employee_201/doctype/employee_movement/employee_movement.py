# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json, datetime
from dateutil.relativedelta import relativedelta
from frappe import _
#from workwise.utils.employee_utils import set_employee_name
from frappe import throw
from frappe.utils import getdate, today, cstr, flt, nowdate, get_datetime
from frappe.model.document import Document
from workwise.payroll.payroll_utils import format_decimal_by_2
from workwise.time_keeping.application_utils import validate_inactive_employee, validate_active_employee
from workwise.time_keeping.timekeeping_task import validate_create_lbentry, gather_total_lb_entries

class EmployeeMovement(Document):
	def validate(self):
		self.clear_fields()
		self.get_sensitivity_level()
		if self.movement_type in ["Job Rotation", "Retirement", "Resignation", "Regularization", "Transfer", "Termination", "Salary Adjustment", "Extension of Services"]:
			validate_inactive_employee(self)
		if self.movement_type in ["Rehire"]:
			validate_active_employee(self)
		self.validate_movement()

	def before_submit(self):
		self.update_movement()

	def before_cancel(self):
		self.revert_movement()

	def clear_fields(self):
		self.old_approvers = None
		self.new_approvers = None
		if self.is_new():
			self.is_processed = None
			self.date_processed = None

	def get_sensitivity_level(self):
		self.sensitivity_level = frappe.db.get_value("Employee", self.employee, 'sensitivity')

	def get_employee_details(self):
		emp = frappe.get_doc("Employee", self.employee)
		self.current_rate = format_decimal_by_2(emp.rate)
		self.new_rate = format_decimal_by_2(emp.rate)
		self.current_minimum_take_home = format_decimal_by_2(emp.min_take_home)
		self.new_minimum_take_home = format_decimal_by_2(emp.min_take_home)
	
	def validate_movement(self):
		movement_type = "cmd_"+cstr(self.movement_type.replace(" ", "_").lower())
		cmd_move = getattr(self, movement_type)
		cmd_move(process="validate")

	def update_movement(self):
		if getdate(self.effective_on) <= getdate(today()):
			movement_type = "cmd_"+cstr(self.movement_type.replace(" ", "_").lower())
			cmd_move = getattr(self, movement_type)
			cmd_move(process="update")

	def revert_movement(self):
		movement_type = "cmd_"+cstr(self.movement_type.replace(" ", "_").lower())
		cmd_move = getattr(self, movement_type)
		cmd_move(process="revert")

	def validate_fields(self, fields):		
		for d in fields:
			if not self.get(d):
				fname = d.replace("_", " ").title()
				frappe.throw(_(" {0} is Required ").format(fname))

	def cmd_job_rotation(self, process):
		if process == "validate":
			fields = ["new_position", "new_job_level"]
			self.validate_fields(fields)
			self.cmd_salary_adjustment(process=process)

		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"position_title": self.new_position if self.new_position else self.current_position,
					"job_level": self.new_job_level if self.new_job_level else self.current_job_level,
					"job_grade": self.new_job_grade if self.new_job_grade else self.current_job_grade,
				})
			self.save_employee(emp)
			self.cmd_salary_adjustment(process=process)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"position_title": self.current_position,
					"job_level": self.current_job_level,
					"job_grade": self.current_job_grade,
				})
			self.revert_employee(emp)
			self.cmd_salary_adjustment(process=process)

	def cmd_retirement(self, process):
		if process == "validate":
			fields = ["retirement_type"]
			self.validate_fields(fields)

		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
				"employment_status": "Retired",
				"is_active": 0,
				"date_retired": getdate(self.effective_on),
				"reports_to": None,
				"approvers": None,
			})

			self.save_employee(emp)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"employment_status": self.current_employment_status,
					"is_active": 1,
					"date_retired": "",
			})

			self.revert_employee(emp)

	def cmd_resignation(self, process):
		if process == "validate":
			fields = ["resignation_type"]
			self.validate_fields(fields)

		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
				"employment_status": "Resigned",
				"is_active": 0,
				"date_resigned": getdate(self.effective_on),
				"reports_to": None,
				"approvers": None,
			})
			self.save_employee(emp)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"employment_status": self.current_employment_status,
					"is_active": 1,
					"date_resigned": "",
				})
			self.revert_employee(emp)

	def cmd_regularization(self, process):
		if process == "validate":			
			self.cmd_salary_adjustment(process=process)

		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"employment_status": self.change_employment_status if self.change_employment_status else self.current_employment_status,
					"is_active": 1,
					"position_title": self.change_position_title if self.change_position_title else self.current_position_title,
				})
			self.save_employee(emp)
			self.cmd_salary_adjustment(process=process)
			self.create_lb_entry()

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"employment_status": self.current_employment_status,
					"is_active": 1,
					"position_title": self.current_position_title,
				})
			self.revert_employee(emp)
			self.cmd_salary_adjustment(process=process)

	def cmd_transfer(self, process):
		if process == "validate":
			fields = ["transfer_type", "new_department", "new_location"]
			self.validate_fields(fields)
			self.cmd_salary_adjustment(process=process)

		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
				"position_title": self.transfer_new_position_title if self.transfer_new_position_title else self.transfer_cur_position_title,
				"company": self.new_company if self.new_company else self.current_company,
				"department": self.new_department if self.new_department else self.current_department,
				"location": self.new_location if self.new_location else self.current_location,
				"job_grade": self.new_job_grade if self.new_job_grade else self.current_job_grade,
			})

			self.save_employee(emp)
			self.cmd_salary_adjustment(process=process)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
				"position_title": self.transfer_cur_position_title,
				"company": self.current_company,
				"department": self.current_department,
				"location": self.current_location,
			})
			self.revert_employee(emp)
			self.cmd_salary_adjustment(process=process)

	def cmd_termination(self, process):
		if process == "validate":
			fields = ["termination_due_to"]
			self.validate_fields(fields)

		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
				"employment_status": "Terminated",
				"is_active": 0,
				"date_terminated": getdate(self.effective_on),
				"reports_to": None,
				"approvers": None,
			})
			self.save_employee(emp)


		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"employment_status": self.current_employment_status,
					"is_active": 1,
					"date_terminated": "",
				})
			self.revert_employee(emp)

	def cmd_salary_adjustment(self, process):
		if process == "validate":
			fields = ["new_rate_type", "new_rate"]
			self.validate_fields(fields)

		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"rate_type": self.new_rate_type if self.new_rate_type else self.current_rate_type,
					"rate": flt(self.new_rate, 2) if self.new_rate else flt(self.current_rate, 2),
					"min_take_home": flt(self.new_minimum_take_home, 2) if self.new_minimum_take_home else flt(self.current_minimum_take_home, 2),
					"is_attendance_base": self.new_attendance_base,
					"cost_center": self.new_cost_center if self.new_cost_center else self.current_cost_center,
					"rate_class": self.new_rate_classification,
				})
			self.save_employee(emp)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"rate_type": self.current_rate_type,
					"rate": flt(self.current_rate, 2),
					"min_take_home": flt(self.current_minimum_take_home, 2),
					"is_attendance_base": self.current_attendance_base,
					"cost_center": self.current_cost_center,
					"rate_class": self.current_rate_classification,
				})
			self.revert_employee(emp)

	def cmd_extension_of_services(self, process):
		if process == "validate":
			fields = ["new_end_of_contract"]
			self.validate_fields(fields)
			if self.current_end_of_contract and self.new_end_of_contract:
				if getdate(self.current_end_of_contract) > getdate(self.new_end_of_contract):
					frappe.throw(_("New End of Contract should not be greater than Current End of Contract"))
				
		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"end_of_contract": self.new_end_of_contract if self.new_end_of_contract else self.current_end_of_contract,
					"date_hired": self.new_date_hired if self.new_date_hired else self.current_date_hired,
					"employment_status": self.new_employment_status if self.new_employment_status else self.employment_status,
				})
			self.save_employee(emp)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"end_of_contract": self.current_end_of_contract,
					"date_hired": self.current_date_hired,
					"employment_status": self.employment_status,
				})
			self.revert_employee(emp)

	def cmd_end_of_contract(self, process):
		if process == "validate":
			fields = ["end_of_contract_due_to"]
			self.validate_fields(fields)

		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"is_active": 0,
					"date_contract_ended": self.effective_on,
					"reports_to": None,
					"approvers": None,
				})
			self.save_employee(emp)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"is_active": 1,
					"date_contract_ended": None,
				})
			self.revert_employee(emp)

	def cmd_rehire(self, process):
		if process == "validate":
			self.effective_on = today()
			if not self.new_biometrics_id:
				frappe.throw(_( 'New Biometrics ID is required' ))

		elif process == "update":
			emp_entry = {}
			emp_flds = frappe.db.sql(""" SELECT `fieldname`, `label`, `fieldtype`, `parent`, `options` FROM `tabDocField` WHERE `parent` = 'Employee' ORDER BY `idx` """, as_dict=True)
			emp_data = frappe.db.sql(""" SELECT * FROM `tabEmployee` WHERE `name` = %(employee)s LIMIT 1 """,{ "employee": self.employee}, as_dict=True)

			for fld in emp_flds:
				if fld['fieldname'] in emp_data[0]:
					if emp_data[0][fld['fieldname']]:
						emp_entry[fld['fieldname']] = emp_data[0][fld['fieldname']]

				if fld['fieldtype'] == 'Table':
					included_flds = []
					emp_entry[fld['fieldname']] = []
					
					table_flds = frappe.db.sql(""" SELECT `fieldname`, `label`, `fieldtype` FROM `tabDocField` WHERE `parent` = %(parent)s AND `fieldtype` NOT IN ('Column Break', 'Section Break') ORDER BY `idx` """,{ "parent": fld['options']}, as_dict=True)
					for tab_fld in table_flds:
						included_flds.append("`"+cstr(tab_fld['fieldname'])+"`")
					table_data = frappe.db.sql(""" SELECT {0} FROM `tab{1}` WHERE `parent` = %(parent)s ORDER BY `idx` """.format(", ".join(included_flds), fld['options']),{ "parent": self.employee }, as_dict=True)

					for tab_dat in table_data:
						emp_entry[fld['fieldname']].append(tab_dat)

			emp_entry['employee_id'] = self.new_employee_id if self.new_employee_id else None
			emp_entry['end_of_contract'] = None
			emp_entry['date_retired'] = None
			emp_entry['date_resigned'] = None
			emp_entry['date_termindated'] = None
			emp_entry['user_id'] = None
			emp_entry['date_contract_ended'] = None
			emp_entry['biometrics_id'] = self.new_biometrics_id
			emp_entry['role'] = self.new_role if self.new_role else emp_data[0]['role']
			emp_entry['email'] = self.new_email if self.new_email else emp_data[0]['email']
			emp_entry['is_active'] = 1
			emp_entry['date_hired'] = today()
			emp_entry['company'] = self.rh_new_company if self.rh_new_company else emp_data[0]['company']
			emp_entry['job_grade'] = self.emp_new_job_grade if self.emp_current_job_grade else emp_data[0]['job_grade']
 
			if emp_entry:
				emp = frappe.get_doc("Employee", self.employee)
				emp.update({
					"is_active": 0,
				})
				emp.save()
				
				new_emp = frappe.new_doc("Employee")
				new_emp.update(emp_entry)
				new_emp.save()

				self.created_employee = new_emp.name
				self.is_processed = 1
				self.date_processed = today()
			else:
				frappe.throw(_("Failed to Rehire Employee. Please try again later"))

		elif process == "revert":
			pass

	def save_employee(self, emp):
		self.add_additional_changes(emp, actiontype='save')

		if emp.save():
			self.is_processed = 1
			self.date_processed = today()

			if self.movement_type in ["Resignation", "Termination", "Retirement", "End of Contract"]:
				frappe.db.commit()
				self.remove_employee_subordinates()
				self.remove_employee_as_approver()

	def revert_employee(self, emp):
		self.add_additional_changes(emp, actiontype='revert')

		if emp.save():
			self.is_processed = 0
			self.date_processed = today()

	def get_lbentries_dates_to_create(self):
		#Get date list to create
		datetoday = str(getdate(nowdate()).year)+'-'+str(getdate(nowdate()).month)+'-01'
		dates_to_create = [getdate(datetoday), getdate(self.effective_on)]
		monthcount_diff = relativedelta(getdate(nowdate()), getdate(self.effective_on)).months
		monthcount_diff = abs(monthcount_diff)
		while monthcount_diff >= 0:
			create_date = getdate(self.effective_on) + relativedelta(months=+monthcount_diff)
			create_date = getdate(str(create_date.year)+"-"+str(create_date.month)+"-01")
			if getdate(self.effective_on) <= create_date <= getdate(nowdate()):
				if create_date not in dates_to_create:
					dates_to_create.append(create_date)
			monthcount_diff -= 1

		return dates_to_create

	def create_lb_entry(self):
		#Create lb entries
		doc_emp = frappe.get_doc("Employee", self.employee)
		if doc_emp.leave_balance_setup:
			lb_setup = frappe.get_doc("Leave Balance Setup", doc_emp.leave_balance_setup)
			lb_sched = frappe.db.sql(""" SELECT * FROM `tabLeave Balance Schedule` WHERE `parent` = %s """,(doc_emp.leave_balance_setup),as_dict=1)
			year_end = getdate(datetime.date(datetime.date.today().year, 12, 31))

			#Gather total lb entries created per employee
			total_lb_entries = gather_total_lb_entries()

			for d in lb_sched:
				is_valid = 0
				dates_to_create = self.get_lbentries_dates_to_create()

				if d.add_from_movement and validate_create_lbentry({'employee': doc_emp.name, 'leave_type': d.leave_type}):
					is_valid = 1

				if d.method != 'Every Month':
					dates_to_create = [getdate(self.effective_on)]

				if d.method == 'Every Month' and not d.is_continuous:
					if d.end_type == 'By Count' and d.by_count_value:
						if self.employee in total_lb_entries and d.leave_type in total_lb_entries[self.employee]:
							lbentry_count = total_lb_entries[self.employee][d.leave_type]
							if lbentry_count >= d.by_count_value:
								valid_setup = 0

					if d.end_type == 'By End of Year' and d.by_end_of_year:
						setup_year_end = getdate(str(d.by_end_of_year)+'-12-31')
						if getdate(self.effective_on) >= getdate(setup_year_end):
							valid_setup = 0

				if is_valid and dates_to_create:
					for dt in dates_to_create:
						lb = frappe.new_doc("LB Entry")
						lb.update({
							"employee": doc_emp.name,
							"employee_name": doc_emp.full_name,
							"posting_date": nowdate(),
							"company": doc_emp.company,
							"leave_type": d.leave_type,
							"balance_type": 'Add',
							"created_from": 'Leave Balance Setup',
							"from_date": dt if d.add_from_movement else nowdate(),
							"to_date": year_end,
							"credits": d.credits,
						})
						lb.flags.ignore_permissions = True
						lb.insert()

	def get_custom_fields(self, target='specific'):
		result = [] 
		filters = {}

		if target == 'specific':
			filters={'movement_type': self.movement_type}

		setup_list = frappe.get_all('Employee Movement Setup', filters=filters)
		for setp in setup_list:
			doc = frappe.get_doc('Employee Movement Setup', setp.name)
			if doc.fields:
				for df in doc.fields:
					result.append({
						'fieldname': df.fieldname,
						'custom_fieldname': 'current_'+str(df.fieldname)
					})
					result.append({
						'fieldname': df.fieldname,
						'custom_fieldname': 'new_'+str(df.fieldname)
					})

		cf_list = []
		if target == 'all':
			cf_list = frappe.get_all('Custom Field', filters={'dt': 'Employee Movement'}, fields=['fieldname'])

		for cf in cf_list:
			if cf.fieldname[:8] == 'current_' or cf.fieldname[:4] == 'new_':
				result.append({
					'fieldname': cf.fieldname,
					'custom_fieldname': str(cf.fieldname)
				})

		return result

	def add_additional_changes(self, emp, actiontype='save'):
		fields = self.get_custom_fields()
		for fd in fields:
			if actiontype=='revert' and fd['custom_fieldname'][:8] == 'current_':
				emp.update({
					fd['fieldname']: self.get(fd['custom_fieldname'])
				})
			if actiontype=='save' and fd['custom_fieldname'][:4] == 'new_':
				emp.update({
					fd['fieldname']: self.get(fd['custom_fieldname'])
				})

	def visible_additional_changes(self):
		result = {
			'show': [],
			'hide': [],
		}

		show_fields = self.get_custom_fields()
		for fd in show_fields:
			result['show'].append(fd['custom_fieldname'])

		hide_fields = self.get_custom_fields('all')
		for fd in hide_fields:
			if fd['custom_fieldname'] not in result['show']:
				result['hide'].append(fd['custom_fieldname'])

		return result

	def remove_employee_subordinates(self):
		if frappe.db.sql(""" SELECT `name` FROM `tabEmployee Subordinates` WHERE `name`=%s """,(self.employee)):
			doc = frappe.get_doc('Employee Subordinates', self.employee)
			if doc:
				doc.subordinates = None
				doc.flags.ignore_permissions = True
				doc.save()

		employees = frappe.db.sql(""" SELECT `parent` FROM `tabSubordinates` WHERE `subordinate`=%s """,(self.employee), as_dict=1)
		for emp in employees:
			employee = frappe.get_doc("Employee Subordinates", emp.parent)
			if employee.subordinates:
				for sub in employee.subordinates:
					if sub.subordinate == self.employee:
						employee.subordinates.remove(sub)
						employee.flags.ignore_permissions = True
						try:
							employee.save()
						except Exception as e:
							pass

	def remove_employee_as_approver(self):
		employees = frappe.db.sql(""" SELECT `parent` FROM `tabEmployee Approvers` WHERE `approver`=%s """,(self.employee), as_dict=1)
		for emp in employees:
			employee = frappe.get_doc("Employee", emp.parent)
			if employee.approvers:
				for app in employee.approvers:
					if app.approver == self.employee:
						employee.approvers.remove(app)
						employee.flags.ignore_permissions = True
						try:
							employee.save()
						except Exception as e:
							pass

@frappe.whitelist()
def run_effective_movement():
	valid = 0
	invalid = 0
	movements = frappe.db.sql(""" SELECT `effective_on`, `name` FROM `tabEmployee Movement` WHERE effective_on<=%s AND is_processed!=1 AND docstatus=1 ORDER BY `modified` ASC """,(today()),as_dict=True)
	for d in movements:
		move = frappe.get_doc("Employee Movement", d.name)
		try:
			move.flags.ignore_permissions = True
			move.update_movement()
			frappe.db.set_value("Employee Movement", move.name, 'is_processed', 1)
			frappe.db.set_value("Employee Movement", move.name, 'date_processed', today())
			print('Valid: '+str(move.name));
			valid += 1
		except Exception as e:
			frappe.db.set_value("Employee Movement", move.name, 'is_processed', 1)
			frappe.db.set_value("Employee Movement", move.name, 'date_processed', today())
			print('Invalid: '+str(move.name)+' Reason: '+str(e));
			invalid += 1
	print('Invalid: '+str(invalid)+"	Valid: "+str(valid));