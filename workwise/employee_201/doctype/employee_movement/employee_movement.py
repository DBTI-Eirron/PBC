# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
#from workwise.utils.employee_utils import set_employee_name
from frappe import throw
from frappe.utils import getdate, today, cstr, flt, nowdate
from frappe.model.document import Document
from workwise.payroll.payroll_utils import format_decimal_by_2
from workwise.time_keeping.application_utils import validate_inactive_employee, validate_active_employee
from workwise.time_keeping.timekeeping_task import validate_create_lbentry

class EmployeeMovement(Document):
	def validate(self):
		if self.movement_type in ["Job Rotation", "Retirement", "Resignation", "Regularization", "Transfer", "Termination", "Salary Adjustment", "Extension of Services"]:
			validate_inactive_employee(self)
		if self.movement_type in ["Rehire"]:
			validate_active_employee(self)
		self.validate_movement()

	def on_submit(self):
		self.update_movement()

	def on_cancel(self):
		self.revert_movement()

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
		if getdate(self.effective_on) <= getdate(nowdate()):
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
				})
			self.save_employee(emp)
			self.cmd_salary_adjustment(process=process)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"position_title": self.current_position,
					"job_level": self.current_job_level,
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

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"employment_status": self.current_employment_status,
					"is_active": 1,
					"position_title": self.current_position_title,
				})
			self.revert_employee(emp)
			self.cmd_salary_adjustment(process=process)
			self.create_lb_entry()

	def cmd_transfer(self, process):
		if process == "validate":
			fields = ["transfer_type", "new_department", "new_location"]
			self.validate_fields(fields)
			self.cmd_salary_adjustment(process=process)

		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"company": self.new_company if self.new_company else self.current_company,
					"department": self.new_department if self.new_department else self.current_department,
					"location": self.new_location if self.new_location else self.current_location,
				})
			self.save_employee(emp)
			self.cmd_salary_adjustment(process=process)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
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
					"is_attendance_base": self.new_attendance_base if self.new_attendance_base else self.current_attendance_base,
					"cost_center": self.new_cost_center if self.new_cost_center else self.current_cost_center,
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
			emp_entry['biometrics_id'] = self.new_biometrics_id
			emp_entry['role'] = self.new_role if self.new_role else emp_data[0]['role']
			emp_entry['email'] = self.new_email if self.new_email else emp_data[0]['email']
			emp_entry['is_active'] = 1
			emp_entry['date_hired'] = today()
			emp_entry['company'] = self.rh_new_company if self.rh_new_company else emp_data[0]['company']
 
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
		if emp.save():
			self.is_processed = 1
			self.date_processed = today()

	def revert_employee(self, emp):
		if emp.save():
			self.is_processed = 0
			self.date_processed = today()

	def run_effective_movement(self):
		movements = frappe.db.sql(""" SELECT effective_on, `name` FROM `tabEmployee Movement` WHERE effective_on <= %s AND is_processed != 1 """,(today()),as_dict=True)
		for d in movements:
			move = frappe.get_doc("Employee Movement", d.name)
			move.submit()

	def create_lb_entry(self):
		doc_emp = frappe.get_doc("Employee", self.employee)
		if doc_emp.leave_balance_setup:
			lb_sched = frappe.db.sql(""" SELECT * FROM `tabLeave Balance Schedule` WHERE `parent` = %s """,(doc_emp.leave_balance_setup),as_dict=1)
			year_end = getdate(datetime.date(datetime.date.today().year, 12, 31))
			for d in lb_sched:
				if validate_create_lbentry({'employee': doc_emp.name, 'leave_type': d.leave_type}):
					lb = frappe.new_doc("LB Entry")
					lb.update({
						"employee": doc_emp.name,
						"employee_name": doc_emp.full_name,
						"posting_date": nowdate(),
						"company": doc_emp.company,
						"leave_type": d.leave_type,
						"balance_type": 'Add',
						"created_from": 'Leave Balance Setup',
						"from_date": nowdate(),
						"to_date": year_end,
						"credits": d.credits,
					})
					lb.flags.ignore_permissions = True
					lb.insert()