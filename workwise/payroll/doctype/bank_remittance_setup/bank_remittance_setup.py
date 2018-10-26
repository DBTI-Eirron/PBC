# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate, add_days, getdate
from frappe import _
from frappe.model.document import Document

class BankRemittanceSetup(Document):
	def validate(self):
		self.validate_duplicate_document()
		self.fill_company()
		self.remove_duplicates()
		self.get_employees_count()
		self.validate_duplicate_employees_with_bank_remittance_setup()

	def on_submit(self):
		pass

	def validate_duplicate_employees_with_bank_remittance_setup(self):
		for d in self.get("employees"):
			setup = frappe.db.sql(""" SELECT DISTINCT BS.`name` FROM `tabBank Remittance Setup` BS JOIN `tabBank Remittance Setup Table` BT ON BS.`name` = BT.`parent` WHERE BS.`docstatus` = 1 AND BS.`company` = %(company)s AND BS.`payroll_period` = %(period)s AND BT.`employee` = %(employee)s """,{ 
				"period": self.payroll_period,
				"company": self.company,
				"employee": d.employee,
			}, as_dict=True)

			if setup:
				frappe.throw(_("Setup for Payroll Period {0} for employee {1} already exists").format(self.payroll_period, d.employee))
			
	def validate_duplicate_document(self):
		documents = frappe.db.sql(""" SELECT `name`, payroll_period, company FROM `tabBank Remittance Setup` WHERE `docstatus` = 1 AND bank = %(bank)s AND company = %(company)s AND payroll_period = %(period)s """,{ 
			"period": self.payroll_period,
			"company": self.company,
			"bank": self.bank,
		}, as_dict=True)

		for d in documents:
			d.name != self.name
			frappe.throw(_("Setup for Payroll Period {0} already exists").format(self.payroll_period))

	def get_employees(self):
		cur_user = frappe.session.user
		if not "Administrator" in frappe.get_roles(cur_user):
			employees = frappe.db.sql(""" SELECT DISTINCT PR.employee, PR.employee_name, PR.net_payroll, BR.bank_account FROM `tabPayroll Register` PR JOIN `tabBank Setup Table` BR ON PR.`employee` = BR.`parent` JOIN `tabEmployee` TE ON PR.`employee` = TE.`name` WHERE TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s) AND TE.`is_active` = 1 AND TE.`on_hold` = 0 AND PR.`period` = %(period)s AND BR.`parenttype` = "Employee" AND BR.`bank_name` = %(bank)s AND BR.`account_type` = %(account_type)s """,{ 
				"period": self.payroll_period,
				"bank": self.bank,
				"account_type": self.bank_account_type,
				"user": cur_user
			}, as_dict=True)
		else:
			employees = frappe.db.sql(""" SELECT DISTINCT PR.employee, PR.employee_name, PR.net_payroll, BR.bank_account FROM `tabPayroll Register` PR JOIN `tabBank Setup Table` BR ON PR.`employee` = BR.`parent` JOIN `tabEmployee` TE ON PR.`employee` = TE.`name` WHERE TE.`is_active` = 1 AND TE.`on_hold` = 0 AND PR.`period` = %(period)s AND BR.`parenttype` = "Employee" AND BR.`bank_name` = %(bank)s AND BR.`account_type` = %(account_type)s """,{ 
				"period": self.payroll_period,
				"bank": self.bank,
				"account_type": self.bank_account_type,
			}, as_dict=True)

		return employees

	def fill_employees(self):
		self.set('employees', [])
		employees = self.get_employees()

		for d in employees:
			i = {
				"employee": d.employee,
				"employee_name": d.employee_name,
				"employee_account": d.bank_account,
				"amount": d.net_payroll,
				"remarks": ""
			}

			row = self.append('employees', {})
			row.update(i)

		self.remove_duplicates()
		self.get_employees_count()

	def get_employees_count(self):
		count = 0
		total_amount = 0.0
		if self.employees:
			for d in self.employees:
				count += 1
				total_amount += d.amount

			self.total_amount = total_amount
			self.total_count = count
		else:
			self.total_amount = 0.00
			self.total_count = 0

	def remove_duplicates(self):
		unique_emp = []
		unique_entries = []
		for d in self.employees:
			if d.employee not in unique_emp:
				unique_emp.append(d.employee);

				i = {
					"employee": d.employee,
					"employee_name": d.employee_name,
					"employee_account": d.employee_account,
					"amount": d.amount,
					"remarks": d.remarks
				}
				unique_entries.append(i);

		self.set('employees', [])
		for ue in unique_entries:
			row = self.append('employees', {})
			row.update(ue)

	def fill_company(self):
		company_bank = frappe.db.sql(""" SELECT `bank_account` FROM `tabBank Setup Table` WHERE `parenttype` = "Company" AND `bank_name` = %(bank)s AND `parent` = %(company)s LIMIT 1""",{ 
			"company": self.company,
			"bank": self.bank,
		}, as_dict=True)

		for d in company_bank:
			self.funding_account = d.bank_account