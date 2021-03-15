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
from workwise.payroll.annualization_utils import get_annual_results

class AnnualizationProcessing(Document):
	def process_annualization(self):
		logs_list = []
		self.validate_filters()
		from_year, to_year = frappe.db.get_value("Payroll Year", self.payroll_year, ["from_date", "to_date"])
		employees = self.get_employee(from_year, to_year)
		registers = self.get_registers(from_year, to_year)
		previous_bir = self.get_previous_bir(from_year, to_year)
		lastpay = self.get_lastpay(from_year, to_year)

		annual_registers = get_annual_entries(employees, registers, previous_bir, lastpay, payroll_year, from_year, to_year)
		self.create_entries(annual_registers, logs_list)

		return self.create_log(logs_list)

	def get_employee(self, from_year, to_year):
		employees = frappe.db.sql("""SELECT TE.`name`, TE.tin, TE.full_name, TE.company, TE.location, TE.mwe_loc, TE.date_hired, TE.date_retired, TE.date_resigned, 
			TE.date_terminated, TE.date_contract_ended, TE.total_yr_days, TE.no_hours, TE.rate, TE.rate_type, TE.sensitivity, 
			(SELECT COUNT(`name`) FROM `tabEmployee External Work History` WHERE parent = TE.`name`) as has_prev
			FROM `tabEmployee` TE 
			LEFT JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name`
			WHERE TE.company = %(company)s 
			AND TE.payroll_schedule = %(schedule)s AND TE.date_hired < %(to_year)s {conditions} 
			ORDER BY TE.full_name ASC """.format( conditions=self.get_employee_conditions() ),
				({ 
					"company": self.company,
					"schedule": self.payroll_schedule,
					"employee": self.employee,
					"from_year": from_year,
					"to_year": to_year,
				}), as_dict=True)

		return employees

	def get_registers(self, from_year, to_year):
		registers = frappe.db.sql("""SELECT PR.name, PR.employee, PR.employee_name, PR.company, PR.posting_date, PR.schedule, PR.gross_payroll,
				PRE.pay_code, PRE.entry_type, PRE.is_taxable, PRE.amount, PR.bonus, PR.monthly_rate, PR.daily_rate FROM `tabPayroll Register Entries` PRE
			INNER JOIN `tabPayroll Register` PR ON PR.`name` = PRE.`parent`
			INNER JOIN `tabPayroll Period` PP ON PR.period = PP.`name`
			WHERE PR.company=%(company)s AND PR.schedule=%(schedule)s AND PR.on_hold = 0 {conditions} 
			AND PP.payroll_year = %(payroll_year)s  """.format( conditions=self.get_conditions() ),
				({ 
					"company": self.company,
					"schedule": self.payroll_schedule,
					"employee": self.employee,
					"payroll_year": self.payroll_year,
					"from_year": from_year,
					"to_year": to_year,
				}), as_dict=True)

		return registers

	def get_previous_bir(self, from_year, to_year):
		previous_bir = frappe.db.sql("""SELECT * FROM `tabBIR2316` 
			WHERE payroll_year = %(payroll_year)s AND document_type = "Previous" {conditions} AND docstatus = 1 """.format( conditions=self.get_reg_conditions() ),
				({ 
					"company": self.company,
					"schedule": self.payroll_schedule,
					"employee": self.employee,
					"payroll_year": self.payroll_year,
				}), as_dict=1)

		return previous_bir

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

	def get_conditions(self):
		conditions = []
		if self.employee:
			conditions.append("PR.employee=%(employee)s")

		return "and {}".format(" and ".join(conditions)) if conditions else ""

	def get_reg_conditions(self):
		conditions = []
		if self.employee:
			conditions.append("employee=%(employee)s")

		return "and {}".format(" and ".join(conditions)) if conditions else ""		

	def get_employee_conditions(self):
		conditions = []
		if self.employee:
			conditions.append("TE.`name`=%(employee)s")

		if self.department:
			lft, rgt = frappe.db.get_value("Department", self.department, ["lft", "rgt"])
			conditions.append(_("( DEPT.`lft` BETWEEN '{0}' AND '{1}' )").format(lft, rgt))

		if self.location:
			conditions.append("TE.location=%(location)s")
		
		if frappe.session.user != "Administrator":
			conditions.append(_("TE.sensitivity IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

		return "AND {}".format(" AND ".join(conditions)) if conditions else ""

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