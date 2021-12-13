# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, cstr
from frappe import _
from frappe.model.document import Document

class RecurringEntry(Document):
	def validate(self):
		self.validate_transaction_type()
		self.remove_duplicates()
		self.validate_weekly()
		self.validate_range_date()
		self.validate_table()

	def validate_transaction_type(self):
		is_rec, is_act = frappe.db.get_value("Transaction Type", self.transaction_type, ["is_recurring", "is_active"])
		if not is_rec:
			frappe.throw(_("Transaction Type is not Allowed for Recurring"))

		if not is_act:
			frappe.throw(_("Transaction Type is not Active"))

	def validate_range_date(self):
		if self.recurring_type == "Range":
			if not self.date_from or not self.date_to:
				frappe.throw(_("Date From and Date To is Required"))

	def validate_table(self):
		if not self.employees:
			frappe.throw(_("No Employee found"))

	def validate_weekly(self):
		if self.frequency in ["3rd", "4th", "5th"]:
			for d in self.employees:
				schedule = frappe.db.get_value("Employee", d.employee, "payroll_schedule")
				if schedule != "Weekly":
					frappe.throw(_("3rd, 4th, 5th is for Weekly Employees only {0}, is not a Weekly Employee").format(d.employee))

	def remove_duplicates(self):
		unique_emp = []
		unique_entries = []
		not_in_sensitivity = []
		total_amount = 0
		for d in self.employees:
			if d.employee not in unique_emp:
				amt = 0
				if not d.amount:
					amt = self.rate
				else:
					amt = d.amount

				allow_row = 1
				if self.sensitivity_level and d.sensitivity_level != self.sensitivity_level:
					allow_row = 0
					not_in_sensitivity.append(str(d.employee)+": "+cstr(d.employee_name)+" Amount: "+str(flt(amt, 2)))

				if allow_row:
					unique_emp.append(d.employee)
					i = {
						"employee": d.employee,
						"employee_name": cstr(d.employee_name),
						"amount": flt(amt),
						"sensitivity_level": d.sensitivity_level if self.sensitivity_level else None,
					}	
					unique_entries.append(i)
					total_amount += flt(amt)

		self.set('employees', [])
		for ue in unique_entries:
			row = self.append('employees', {})
			row.update(ue)
		self.total_amount = total_amount

		if not_in_sensitivity:
			not_in_sensitivity = ', <br>'.join(not_in_sensitivity)
			frappe.throw(_("The following Employees does not belong to {0} Sensitivity Level: <br>{1}").format(self.sensitivity_level, not_in_sensitivity))

	def filter_add(self):
		if not self.company:
			frappe.throw(_("Company is Required"))

		clist, conditions = [], ""
		if frappe.session.user != "Administrator":
			clist.append("(TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s) OR TE.sensitivity IS NULL)")

		if self.sensitivity_level:
			clist.append("TE.sensitivity = %(sensitivity)s")

		conditions = "and {}".format(" and ".join(clist)) if clist else ""

		if self.filter_value and self.filter_type:
			entries = []
			employees = ""
			if self.filter_type == 'Employee':
				employees = frappe.db.sql("""SELECT TE.`name`, TE.`full_name`, TE.`sensitivity` FROM `tabEmployee` TE WHERE TE.company = %(company)s  
						AND TE.`name` = %(filter_value)s AND TE.is_active = 1 {conditions} 
						ORDER BY TE.last_name, TE.first_name""".format( conditions=conditions ),{ 
					"company": self.company,
					"filter_value": self.filter_value,
					"user": frappe.session.user,
					"sensitivity": self.sensitivity_level,
				}, as_dict=True)

				if not employees:
					frappe.throw(_(" Employee may be inactive or does not belong to Company "))
				else:
					if self.sensitivity_level and employees[0].sensitivity != self.sensitivity_level:
						frappe.throw(_(" Employee {0} does not belong to {1} Sensitivty Level ".format(self.filter_value, self.sensitivity_level)))

			elif self.filter_type == 'Department':
				lft, rgt = frappe.db.get_value("Department", self.filter_value, ["lft", "rgt"])
				employees = frappe.db.sql("""SELECT TE.`name`, TE.`full_name`, TE.`sensitivity` FROM `tabEmployee` TE 
					LEFT JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name`
					WHERE TE.company = %(company)s AND TE.is_active = 1
					AND TE.department = %(filter_value)s {conditions} 
					ORDER BY TE.last_name, TE.first_name""".format( conditions=conditions ),{ 
					"company": self.company,
					"filter_value": self.filter_value,
					"user": frappe.session.user,
					"sensitivity": self.sensitivity_level,
					"lft": lft,
					"rgt": rgt,
				}, as_dict=True)

				if not employees:
					frappe.throw(_(" No Active Employee found for Company {0} and Department {1} with Sensitivty Level of {2} ".format(self.company, self.filter_value, self.sensitivity_level)))

			elif self.filter_type == 'Location':
				employees = frappe.db.sql("""SELECT TE.`name`, TE.`full_name`, TE.`sensitivity` FROM `tabEmployee` TE WHERE TE.company = %(company)s  
						AND TE.location = %(filter_value)s AND TE.is_active = 1 {conditions} 
						ORDER BY TE.last_name, TE.first_name""".format( conditions=conditions ),{  
					"company": self.company,
					"filter_value": self.filter_value,
					"user": frappe.session.user,
					"sensitivity": self.sensitivity_level,
				}, as_dict=True)

				if not employees:
					frappe.throw(_(" No Active Employee found for Company {0} and Location {1} with Sensitivty Level of {2} ".format(self.company, self.filter_value, self.sensitivity_level)))
	
			if employees:
				for d in employees:
					row = {
						"employee": d.name,
						"employee_name": cstr(d.full_name),
						"amount": flt(self.rate),
						"sensitivity_level": d.sensitivity if self.sensitivity_level else None,
					}
					entries.append(row);

				for d in entries:
					row = self.append('employees', {})
					row.update(d)
			else:
				frappe.throw(_(" You dont have access to this employee "))
		else:
			frappe.throw(_(" Input Filter Value and Filter Type "))

	def filter_add_company(self):
		if self.company:
			entries = []
			employees = ""

			clist, conditions = [], ""
			if frappe.session.user != "Administrator":
				clist.append("sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s)")
			
			if self.sensitivity_level:
				clist.append("sensitivity = %(sensitivity)s")

			conditions = "and {}".format(" and ".join(clist)) if clist else ""

			if self.company:
				employees = frappe.db.sql(""" SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s {conditions} 
					ORDER BY last_name, first_name """.format( conditions=conditions ),{ 
					"company": self.company,
					"filter_value": self.filter_value,
					"user": frappe.session.user,
					"sensitivity": self.sensitivity_level,
				}, as_dict=True)
				
			if employees:
				for d in employees:
					row = {
						"employee": d.name,
						"employee_name": d.full_name,
						"amount": self.rate,
						"sensitivity_level": d.sensitivity if self.sensitivity_level else None,
					}
				
					entries.append(row);

			for d in entries:
				row = self.append('employees', {})
				row.update(d)
		else:
			frappe.throw(_("Company is Required"))

	def filter_reset(self):
		self.set('employees', [])