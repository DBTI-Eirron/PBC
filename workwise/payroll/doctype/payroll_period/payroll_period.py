# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import msgprint, _
from frappe.model.naming import make_autoname
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, comma_or, get_fullname, nowdate, getdate
from frappe.model.document import Document

class PayrollPeriod(Document):
	def autoname(self):
		pay_year = getdate(self.payroll_date).strftime("%Y")
		from_year = getdate(self.from_date).strftime("%Y")
		from_month = getdate(self.from_date).strftime("%b")
		from_day = getdate(self.from_date).strftime("%d")
		to_year = getdate(self.to_date).strftime("%Y")
		to_month = getdate(self.to_date).strftime("%b")
		to_day = getdate(self.to_date).strftime("%d")
		abbr = frappe.get_value("Company", self.company, "abbr")
		self.name = from_month+""+from_day+" "+to_month+""+to_day+" - "+abbr+pay_year

	def validate(self):
		self.validate_days()
		self.validate_frequency()
		self.validate_approval_cutoff()

	def validate_approval_cutoff(self):
		if getdate(self.approval_cutoff) <= getdate(self.attendance_to):
			frappe.throw(_("Last Cutoff Date of Approval should be greater than To Date"))

	def validate_frequency(self):
		if self.schedule == "Monthly":
			self.frequency = "2nd"
			frappe.msgprint("Frequency Changed to ( 2nd ) because Schedule was set to Monthly")

		if self.schedule != "Weekly":
			if self.frequency ==( "3rd" or "4th" or "5th"):
				self.frequency = "2nd" 
				frappe.msgprint("Frequency Changed to ( 2nd ) because (3rd 4th 5th) is not allowed for Monthly and Semi-Monthly")

		if self.schedule == "Weekly":
			if not self.weekly_set:
				frappe.throw(_("Weekly Set is Required if Weekly Schedule"))

			self.validate_duplicate_set()

	def validate_duplicate_set(self):
		duplicate = frappe.db.sql(""" SELECT `name` FROM `tabPayroll Period` 
			WHERE name != %s AND company = %s AND frequency = %s AND weekly_set = %s AND schedule = "Weekly" """, (self.name, self.company, self.frequency, self.weekly_set),as_dict=1)
		if duplicate:
			frappe.throw(_("{0} Frequency already exist in {1} Weekly Set").format(self.frequency ,self.weekly_set))

			
	def validate_days(self):
		difference = date_diff(self.to_date, self.from_date)
		difference += 1
		if self.schedule == "Monthly":
			if not difference > 27:
				frappe.throw(_("Monthly Schedule Should be Greater than {0} days ").format(difference))
		if difference > 31:
			frappe.throw("Days Should not be Greater than 31 days ")

		if self.schedule == "Weekly":
			if difference > 7:
				frappe.throw("Days Should not be Greater than 7 days for Weekly Period")
	
	def remove_payslips(self):

		log = frappe.new_doc("Payroll Process Logs")
		log.update({
			"user_id": frappe.session.user, 
			"datetime": frappe.utils.now(), 
			"remarks": "Payroll Period "+ self.name +" Deleted Payslips",
		})
		log.insert()
		msgprint("Payslips DELETED")

	def make_payslips(self):
		log = frappe.new_doc("Payroll Process Logs")
		log.update({
			"user_id": frappe.session.user, 
			"datetime": frappe.utils.now(), 
			"remarks": "Payroll Period "+ self.name +" Created Payslips",
		})
		log.insert()

		if self.status == "Open":
			frappe.throw("Please Close Period Before Creating Payslips")
		else:
			frappe.db.sql(""" DELETE FROM `tabMy Payslip` WHERE payroll_period = %(period)s """,{ 
					"period": self.name,
				}, as_dict=True)
			frappe.db.commit()

			employees = frappe.db.sql(""" SELECT `name`, full_name, location, company, sss_no, phic_no, hdmf_no, tin, user_id
			FROM tabEmployee WHERE `name` IN (SELECT employee FROM `tabPayroll Register` WHERE period = %s ) AND on_hold != 1  ORDER BY last_name, first_name  """, self.name,as_dict=1)

			for emp in employees:
				payroll_date, net_payroll, total_incomes, total_deductions = "", 0, 0, 0
				register = frappe.db.sql(""" SELECT PRE.*, PR.on_hold, PR.posting_date, PR.net_payroll, PR.total_deduction, PR.total_income FROM `tabPayroll Register`  PR
					INNER JOIN `tabPayroll Register Entries` PRE ON PRE.parent = PR.`name`
	 				WHERE period = %(period)s and employee = %(employee)s """,{ 
						"period": self.name,
						"employee": emp.name,
					}, as_dict=True)

				if register:
					letter_head = frappe.db.get_value("Company", emp.company, "default_letter_head")
					ps = frappe.new_doc("My Payslip")
					ps.update({
						"owner": emp.user_id, "employee": emp.name, "payroll_period": self.name, 
						"employee_name": emp.full_name, "company": emp.company,
						"sss_no": emp.sss_no, "phic_no": emp.phic_no, "hdmf_no": emp.hdmf_no, "tin": emp.tin,
					});

					for d in register:
						if d.pay_type == "Income":
							ps.append("payslip_incomes", {
								"description": d.pay_description,
								"amount": d.amount,
							})
						elif d.pay_type == "Deduction":
							ps.append("payslip_deductions", {
								"description": d.pay_description,
								"amount": d.amount,
							})

						payroll_date = d.posting_date
						net_payroll = d.net_payroll
						total_incomes = d.total_income
						total_deductions = d.total_deduction

					ps.update({
						"payroll_date": payroll_date,
						"letter_head": letter_head,
						"net_payroll": net_payroll,
						"total_income": total_incomes,
						"total_deduction": total_deductions
					});
					ps.insert()
			
			msgprint("Payslips Created")
