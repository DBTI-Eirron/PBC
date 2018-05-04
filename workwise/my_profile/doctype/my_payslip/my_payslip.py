# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class MyPayslip(Document):

	def get_payslip(self):
		period_details = frappe.db.sql("""SELECT * FROM `tabPayroll Period` WHERE `name` = %s LIMIT 1""",( self.payroll_period ), as_dict=1)
		for pd in period_details:
			if pd.status != 'Closed':
				frappe.throw("Payroll Period Must Be Closed")

			self.period_from = pd.from_date
			self.period_to = pd.to_date

		#frappe.throw( ("{0}").format(frappe.session.user) )
		employee_details = frappe.db.sql("""SELECT * FROM `tabEmployee` WHERE user_id = %s LIMIT 1""",( frappe.session.user ), as_dict=1)
		employee = ""
		for ed in employee_details:
			employee = ed.name
			self.employee = ed.name
			self.employee_name = ed.full_name
			self.sss_no = ed.sss_no
			self.phic_no = ed.phic_no
			self.hdmf_no = ed.hdmf_no
			self.tin = ed.tin

		payroll_details = frappe.db.sql("""SELECT PRE.pay_description, PRE.pay_type, PRE.amount FROM `tabPayroll Register` PR 
			INNER JOIN `tabPayroll Register Entries` PRE ON PRE.parent = PR.`name`
		 	WHERE period = %s AND employee = %s AND PRE.pay_type != 'None' """,( self.payroll_period, employee), as_dict=1)
		
		incomes = []
		deductions = []

		for payd in payroll_details:
			if payd.pay_type == "Income":
				entry = {
					"description": payd.pay_description,
					"amount": payd.amount,
				}
				incomes.append(entry);
			else:
				entry = {
					"description": payd.pay_description,
					"amount": payd.amount,
				}
				deductions.append(entry);

			self.set('payslip_incomes', [])
			self.set('payslip_deductions', [])
			
			for inc in incomes:
				row = self.append('payslip_incomes', {})
				row.update(inc)

			for ded in deductions:
				row = self.append('payslip_deductions', {})
				row.update(ded)

		totals_payroll = frappe.db.sql("""SELECT net_payroll, total_deduction, total_income FROM `tabPayroll Register` 
		 	WHERE period = %s AND employee = %s LIMIT 1 """,( self.payroll_period, employee), as_dict=1)

		for tp in totals_payroll:
			self.net_payroll = tp.net_payroll
			self.total_incomes = tp.total_income
			self.total_deduction = tp.total_deduction
