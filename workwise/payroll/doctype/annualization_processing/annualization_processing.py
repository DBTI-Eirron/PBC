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
from workwise.payroll.annualization_utils import get_annual_results, get_annual_employees, get_annual_registers, get_annual_prev2316

class AnnualizationProcessing(Document):
	def process_annualization(self):
		logs_list = []
		self.validate_filters()
		from_year, to_year = frappe.db.get_value("Payroll Year", self.payroll_year, ["from_date", "to_date"])
		employees = get_annual_employees(self.employee, self.company, self.department, self.location, self.payroll_schedule, from_year, to_year)
		registers = get_annual_registers(self.employee, self.company, self.payroll_schedule, self.payroll_year, True)
		previous_bir = get_annual_prev2316(self.employee, self.payroll_year)
		lastpay = self.get_lastpay(from_year, to_year)

		annual_registers = get_annual_results(employees, registers, previous_bir, lastpay, self.payroll_year, from_year, to_year)
		self.create_entries(annual_registers, logs_list)
		
		for annual_reg in annual_registers:
			self.create_annualization_processing_logs(annual_reg)

		return self.create_log(logs_list)

	def get_lastpay(self, from_year, to_year):
		c_list = []
		if self.employee:
			c_list.append("employee=%(employee)s")
		conditions = "and {}".format(" and ".join(c_list)) if c_list else ""

		lastpay = frappe.db.sql("""SELECT employee, LPR.transaction_type, LPR.amount, LPR.type FROM  `tabLast Pay Entry` LPE 
			INNER JOIN `tabLast Pay Register` LPR ON LPR.parent = LPE.`name`
			WHERE payroll_year = %(payroll_year)s 
			AND LPE.docstatus = 1 {conditions} """.format( conditions=conditions ),
				({ 
					"employee": self.employee,
					"payroll_year": self.payroll_year,
				}), as_dict=1)

		return lastpay

	def create_entries(self, annual_registers, logs_list):
		signatory = self.get_signatory(frappe.session['user'])
		for ar in annual_registers:
			frappe.db.sql("""DELETE FROM `tabAnnualization Register` 
				WHERE employee = %s AND payroll_year = %s """,(ar.employee, ar.payroll_year), as_dict=1)

			ar["signatory"]=signatory

			register = frappe.new_doc("Annualization Register")
			register.update(ar)

			if register.insert():
				logs_list.append( cstr(register.employee)+": "+cstr(register.employee_name) )

	def get_signatory(self, user):
		signatory = ""
		sign = frappe.db.sql(""" SELECT `name`, `user_id`, full_name FROM `tabEmployee` 
			WHERE user_id = %s AND user_id != "" AND user_id is not null LIMIT 1""",(user), as_dict=1)
		for d in sign:
			signatory = d.full_name

		return signatory

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

	def create_annualization_processing_logs(self, header):
		pr = frappe.new_doc("Annualization Processing Logs")
		pr.update(header)
		pr.update({
			'company': self.company,
			'payroll_year': self.payroll_year,
			'payroll_schedule': self.payroll_schedule,
			'employee': self.employee,
			'department': self.department,
			'location': self.location,
			'user': frappe.session.user,
			'user_name': frappe.db.get_value("User",{"name":frappe.session.user}, "full_name"),
			'user_ip': frappe.local.request_ip,
		})
		pr.flags.ignore_permissions = True
		pr.insert()