# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, cstr, today
from frappe import _
from frappe.model.document import Document
from workwise.payroll.payroll_utils import get_rates

class WageOrder(Document):
	def validate(self):
		self.validate_employees()

	def on_submit(self):
		self.update_rates()

	def on_cancel(self):
		self.revert_rates()

	def update_rates(self):
		if getdate(self.effective_on) <= getdate(nowdate()):
			for d in self.get("wage_order"):
				set_rate = d.new_rate
				if d.new_rate <= 0:
					set_rate = d.current_rate
				emp = frappe.get_doc("Employee", d.employee)
				emp.update({
					"rate": flt(set_rate, 8),
				})
				emp.save()

	def revert_rates(self):
		if getdate(self.effective_on) <= getdate(nowdate()):
			for d in self.get("wage_order"):
				emp = frappe.get_doc("Employee", d.employee)
				emp.update({
					"rate": flt(d.current_rate, 8),
				})
				emp.save()

	def validate_employees(self):
		unique_emp = []
		unique_entries = []

		if not self.get("wage_order"):
			frappe.throw(_("Employees required"))

		for d in self.get("wage_order"):
			is_active = frappe.get_value("Employee", d.employee, "is_active")
			if not is_active:
				frappe.throw(_("Employee {0} is not active").format(d.employee))
			if str(d.employee) not in unique_emp:
				unique_emp.append(str(d.employee));

				i = {
					"employee": d.employee,
					"employee_name": d.employee_name,
					"rate_type": d.rate_type,
					"current_rate": d.current_rate,
					"new_rate": d.new_rate
				}
				unique_entries.append(i);

		self.set('wage_order', [])
		for ue in unique_entries:
			row = self.append('wage_order', {})
			row.update(ue)

	def reset_employees(self):
		self.set('wage_order', [])

	def get_employees(self):
		employees = frappe.db.sql("""SELECT TE.`name`, TE.`full_name`, TE.`rate_type`, TE.`rate`, 
			TL.`name` as location, TL.`min_wage`, TE.`total_yr_days`, TE.`no_hours`
			FROM `tabEmployee` TE INNER JOIN `tabLocation` TL ON TE.`location` = TL.`name`
			WHERE TE.is_active = 1 AND TE.company = %(company)s AND TE.`sensitivity` = %(sensitivity)s {conditions}
			ORDER BY TE.`full_name` """.format(conditions=self.get_conditions()),{ 
			"company": self.company,
			"sensitivity": self.sensitivity,
		}, as_dict=True)
		
		return employees

	def get_conditions(self):
		conditions = []
		if self.filter_type == "Employee":
			conditions.append(_("TE.`name` = '{0}'").format(self.filter_value))

		if self.filter_type == "Location":
			conditions.append(_("TE.`location` = '{0}'").format(self.filter_value))

		if self.filter_type == "Department":
			conditions.append(_("TE.`Department` = '{0}'").format(self.filter_value))

		return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

	def filter_add(self):
		if not self.company:
			frappe.throw(_("Company is Required"))

		if not self.sensitivity:
			frappe.throw(_("Sensitivity is Required"))

		if self.filter_value and self.filter_type:
			entries = []
			curr_emp = []
			employees = self.get_employees()
			
			for d in self.get("wage_order"):
				curr_emp.append(d.employee)

			if employees:
				for emp in employees:
					#rates = get_rates(emp)
					#if rates['daily_rate'] <= emp.min_wage:
					if emp.name not in curr_emp:
						row = {
							"employee": emp.name,
							"employee_name": emp.full_name,
							"rate_type": emp.rate_type,
							"current_rate": emp.rate,
						}
						entries.append(row)

				for e in entries:
					row = self.append('wage_order', {})
					row.update(e)
			else:
				frappe.throw(_(" No Employee Found "))	
		else:
			frappe.throw(_(" Input Filter Value and Filter Type "))