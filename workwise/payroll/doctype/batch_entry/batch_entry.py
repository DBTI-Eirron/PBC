# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document

class BatchEntry(Document):
	def validate(self):
		self.validate_transaction_type()
		self.remove_duplicates()	

	def validate_transaction_type(self):
		is_bat, is_act = frappe.db.get_value("Transaction Type", self.transaction_type, ["is_batch", "is_active"])
		if not is_bat:
			frappe.throw(_("Transaction Type is not Allowed for Batch"))

		if not is_act:
			frappe.throw(_("Transaction Type is not Active"))

	def remove_duplicates(self):
		unique_emp = []
		unique_entries = []
		for d in self.employees:
			if d.employee not in unique_emp:
				unique_emp.append(d.employee);
				amt = 0

				if not d.amount:
					amt = self.rate
				else:
					amt = d.amount

				i = {
					"employee": d.employee,
					"employee_name": d.employee_name,
					"amount": amt
				}	
				unique_entries.append(i);

		self.set('employees', [])
		for ue in unique_entries:
			row = self.append('employees', {})
			row.update(ue)

	def filter_add(self):
		cur_user = frappe.session.user
		if not self.company:
			frappe.throw(_("Company is Required"))

		if self.filter_value and self.filter_type:
			entries = []
			employees = ""
			if self.filter_type == 'Employee':
				if not "Administrator" in frappe.get_roles(cur_user):
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s  AND `name` = %(filter_value)s AND sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
												INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s) ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
						"user": frappe.session.user,
					}, as_dict=True)
				else:
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s  AND `name` = %(filter_value)s AND sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
												INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`) ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
					}, as_dict=True)
			elif self.filter_type == 'Department':
				if not "Administrator" in frappe.get_roles(cur_user):
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s  AND department = %(filter_value)s AND sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
												INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s) ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
						"user": frappe.session.user,
					}, as_dict=True)
				else:
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s  AND department = %(filter_value)s AND sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
												INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`) ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
					}, as_dict=True)
			elif self.filter_type == 'Location':
				if not "Administrator" in frappe.get_roles(cur_user):
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s  AND location = %(filter_value)s AND sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
												INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s) ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
					}, as_dict=True)
				else:
					employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s  AND location = %(filter_value)s AND sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
												INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`) ORDER BY last_name, first_name""",{ 
						"company": self.company,
						"filter_value": self.filter_value,
						"user": frappe.session.user,
					}, as_dict=True)
			
			if employees:
				for d in employees:
					row = {
						"employee": d.name,
						"employee_name": d.full_name,
						"amount": self.rate
					}
				
					entries.append(row);

				for d in entries:
					row = self.append('employees', {})
					row.update(d)
			else:
				frappe.throw(_(" You dont have access to this employee "))
		else:
			frappe.throw(_(" Input Filter Value and Filter Type "))

	def filter_reset(self):
		self.set('employees', [])

	def validate_user_sensitivity_level(self):
		pass