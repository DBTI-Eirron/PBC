# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from calendar import monthrange
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from frappe import _
from frappe.model.document import Document
from workwise.payroll.payroll_utils import get_transaction_map, get_rates, get_location_map, get_company_map
from workwise.payroll.annualization_utils import get_annual_results, get_annual_employees, get_annual_prev2316

class AnnualizationProcessing(Document):
	def process_annualization(self):
		logs_list = []
		self.validate_filters()
		from_year, to_year = frappe.db.get_value("Payroll Year", self.payroll_year, ["from_date", "to_date"])
		employees = get_annual_employees(self.employee, self.company, self.department, self.location, self.payroll_schedule, from_year, to_year)
		registers = get_annual_registers(self.employee, self.company, self.payroll_schedule, self.payroll_year)
		previous_bir = get_annual_prev2316(self.employee, self.payroll_year)
		lastpay = self.get_lastpay(from_year, to_year)

		annual_registers = get_annual_entries(employees, registers, previous_bir, lastpay, payroll_year, from_year, to_year)
		self.create_entries(annual_registers, logs_list)

		return self.create_log(logs_list)

	def get_lastpay(self, from_year, to_year):
		lastpay = frappe.db.sql("""SELECT employee, LPR.transaction_type, LPR.amount, LPR.type FROM  `tabLast Pay Entry` LPE 
			INNER JOIN `tabLast Pay Register` LPR ON LPR.parent = LPE.`name`
			WHERE payroll_year = %(payroll_year)s AND remarks != 'On Hold Payroll' {conditions} """.format( conditions=self.get_reg_conditions() ),
				({ 
					"company": self.company,
					"schedule": self.payroll_schedule,
					"employee": self.employee,
					"payroll_year": self.payroll_year,
				}), as_dict=1)

		return lastpay

	def create_entries(self, annual_registers, logs_list):
		for ar in annual_registers:
			register = frappe.new_doc("Annualization Register")
			register.update(ar)
			if register.insert():
				logs_list.append( cstr(register.employee)+": "+cstr(register.employee_name) )
				
	def validate_filters(self):
		if not self.company:
			frappe.throw(" Company is Required for Annualization Processing")

		if not self.payroll_year:
			frappe.throw(" Year is Required for Annualization Processing")

		if not self.payroll_schedule:
			frappe.throw(" Payroll Schedule is Required for Annualization Processing")

	def create_log(self, logs_list):
		log = "<p>" + _("No Annualization Registers Created") + "</p>"
		if logs_list:
			log = "<p>" + _("Annualization Registers Created") + "</p>"
			add_log = '<br>'.join(logs_list)
			log += add_log

		return log