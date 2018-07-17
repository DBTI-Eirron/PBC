	# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
#from workwise.utils.employee_utils import set_employee_name
from frappe import throw
from frappe.utils import getdate, today, cstr
from frappe.model.document import Document

class EmployeeMovement(Document):
	def validate(self):
		self.validate_movement()

	def on_submit(self):
		self.update_movement()

	def on_cancel(self):
		self.revert_movement()
	
	def validate_movement(self):
		movement_type = "cmd_"+cstr(self.movement_type.replace(" ", "_").lower())
		cmd_move = getattr(self, movement_type)
		cmd_move(process="validate")

	def update_movement(self):
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
					"position_title": self.new_position,
					"job_level": self.new_job_level,
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

	def cmd_retirement(self, process):
		if process == "validate":
			fields = ["retirement_type"]
			self.validate_fields(fields)

		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)

			
			self.save_employee(emp)
			
			#disable user id
			us = frappe.get_doc("User", emp.user_id)
			us.update({
					"new_password": us.frappe_userid,
				})
			us.save()

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
			fields = ["regularization_type"]
			self.validate_fields(fields)
			self.cmd_salary_adjustment(process=process)

		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"employment_status": "Regular",
					"is_active": 0,
				})
			self.save_employee(emp)
			self.cmd_salary_adjustment(process=process)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"employment_status": self.current_employment_status,
					"is_active": 1,
				})
			self.revert_employee(emp)

	def cmd_transfer(self, process):
		if process == "validate":
			fields = ["transfer_type", "new_department", "new_location"]
			self.validate_fields(fields)
			self.cmd_salary_adjustment(process=process)

		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"department": self.new_department,
					"location": self.new_location,
				})
			self.save_employee(emp)
			self.cmd_salary_adjustment(process=process)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"department": self.current_department,
					"location": self.current_location,
				})
			self.revert_employee(emp)

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
					"rate_type": self.new_rate_type,
					"rate": self.new_rate,
					"min_take_home": self.new_minimum_take_home if self.new_minimum_take_home else self.current_minimum_take_home,
					"is_attendance_base": self.new_attendance_base if self.new_attendance_base else self.current_attendance_base,
				})
			self.save_employee(emp)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"rate_type": self.current_rate_type,
					"rate": self.current_rate,
					"min_take_home": self.current_minimum_take_home,
					"is_attendance_base": self.current_attendance_base,
				})
			self.revert_employee(emp)

	def cmd_extension_of_services(self, process):
		if process == "validate":
			fields = ["new_end_of_contract"]
			self.validate_fields(fields)
			if getdate(self.current_end_of_contract) > getdate(self.new_end_of_contract):
				frappe.throw(_("New End of Contract should not be greater than Current End of Contract"))
				
		elif process == "update":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"end_of_contract": self.new_end_of_contract,
				})
			self.save_employee(emp)

		elif process == "revert":
			emp = frappe.get_doc("Employee", self.employee)
			emp.update({
					"end_of_contract": self.current_end_of_contract,
				})
			self.revert_employee(emp)

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