# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, calendar, time
from time import strptime
from frappe import msgprint, _
from frappe.model.naming import make_autoname
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, comma_or, get_fullname, nowdate, getdate
from frappe.model.document import Document

class PayrollPeriod(Document):
	def autoname(self):
		#pay_year = getdate(self.payroll_date).strftime("%Y")
		pay_year = self.payroll_year
		from_year = getdate(self.from_date).strftime("%Y")
		from_month = getdate(self.from_date).strftime("%b")
		from_day = getdate(self.from_date).strftime("%d")
		to_year = getdate(self.to_date).strftime("%Y")
		to_month = getdate(self.to_date).strftime("%b")
		to_day = getdate(self.to_date).strftime("%d")
		abbr = frappe.get_value("Company", self.company, "abbr")
		if self.period_group:
			self.name = from_month+""+from_day+" "+to_month+""+to_day+" - "+self.period_group+" - "+abbr+pay_year
		else:
			self.name = from_month+""+from_day+" "+to_month+""+to_day+" - "+abbr+pay_year

	def validate(self):
		self.validate_days()
		self.validate_frequency()
		self.validate_approval_cutoff()
		self.validate_period_group()
		self.validate_payroll_period()

	def validate_payroll_period(self):
		validate_payroll_date = frappe.db.get_single_value('Payroll Settings', 'validate_payroll_date')
		if getdate(self.payroll_date) <= getdate(self.attendance_from) and validate_payroll_date:
			frappe.throw(_("Payroll Date should be higher than the cut-off dates."))
		if getdate(self.payroll_date) <= getdate(self.attendance_to) and validate_payroll_date:
			frappe.throw(_("Payroll Date should be higher than the cut-off dates."))

	def validate_approval_cutoff(self):
		if getdate(self.approval_cutoff) <= getdate(self.attendance_to):
			frappe.throw(_("Last Cutoff Date of Approval should be greater than To Date"))

	def validate_frequency(self):
		if self.schedule == "Monthly":
			self.frequency = "2nd"
			frappe.msgprint("Frequency Changed to ( 2nd ) because Schedule was set to Monthly")

		if self.schedule != "Weekly":
			if self.frequency == "3rd" or self.frequency == "4th" or self.frequency == "5th":
				self.frequency = "2nd" 
				frappe.msgprint("Frequency Changed to ( 2nd ) because (3rd 4th 5th) is not allowed for Monthly and Semi-Monthly")

		if self.schedule == "Weekly":
			if not self.weekly_set:
				frappe.throw(_("Weekly Set is Required if Weekly Schedule"))

			self.validate_duplicate_set()

		if self.is_special:
			if self.frequency != "Special":
				frappe.throw(_(str("Frequency must be Special")))

		if self.frequency == "Special":
			self.is_special = 1

	def validate_duplicate_set(self):
		duplicate = frappe.db.sql(""" SELECT `name` FROM `tabPayroll Period` 
			WHERE name != %s AND company = %s AND frequency = %s AND weekly_set = %s AND schedule = "Weekly" """, (self.name, self.company, self.frequency, self.weekly_set),as_dict=1)
		if duplicate:
			frappe.throw(_("{0} Frequency already exist in {1} Weekly Set").format(self.frequency ,self.weekly_set))

	def validate_period_group(self):
		strict_pg = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')
		if strict_pg:
			if not self.period_group:
				frappe.throw("Period Group is Required for Strict use of Period Group")

		if self.period_group and self.schedule == "Weekly":
			if self.weekly_set:
				wkpg = frappe.db.get_value("Weekly Set", self.weekly_set, "period_group")
				if not wkpg:
					frappe.throw(_("Period Group for Weekly Set is required if Period Group is set"))
				else:
					if wkpg != self.period_group:
						frappe.throw(_("Invalid Weekly Set {0}, Weekly Set is for Period Group {1}").format(self.weekly_set, wkpg))

		if self.weekly_set and not self.period_group:
			wkpg_x = frappe.db.get_value("Weekly Set", self.weekly_set, "period_group")
			if wkpg_x:
				frappe.throw(_("Period Group is required for Weekly Set with Period Group"))

	def validate_days(self):
		if not self.is_special:
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
		if log.insert():
			frappe.db.sql(""" DELETE FROM `tabMy Payslip` WHERE payroll_period = %(period)s """,{ 
					"period": self.name,
				}, as_dict=True)

			msgprint("Payslips DELETED")

	def get_leave_balance(self,balances,leave_type,emp):
		balance_dict = []
		for lt in leave_type:
			valid_entry = {}
			less_entry = {}
			add, less, total_balance = 0, 0, 0
			min_date = None
			for d in balances:
				if d.employee == emp and (d.leave_type == lt.name or d.deduct_credits_to == lt.name):
					if d.balance_type == "Add":
						if lt.name == d.leave_type:
							if d.name not in valid_entry:
								valid_entry[d.name] = {
									"credits": d.credits,
									"from": getdate(d.from_date),
									"to": getdate(d.to_date),
								}
					else:
						if d.deduct_credits_to == lt.name:
							if d.name not in less_entry:
								less_entry[d.name] = {
									"used": 0,
									"credits": d.credits,
									"from": getdate(d.from_date),
									"to": getdate(d.to_date),
								}

			for vl in valid_entry:
				to_less = 0
				for le in less_entry:
					if valid_entry[vl]['credits'] > 0 and not less_entry[le]['used']:
						if ( valid_entry[vl]['from'] <= less_entry[le]['from'] <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= less_entry[le]['to'] <= valid_entry[vl]['to'] ):
							to_less += less_entry[le]['credits']
							less_entry[le]['used'] = 1
				valid_entry[vl]['credits'] -= to_less
				if ( valid_entry[vl]['from'] <= getdate(self.to_date) <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= getdate(self.to_date) <= valid_entry[vl]['to'] ):
					total_balance += valid_entry[vl]['credits']

			if total_balance <= 0:
				total_balance = 0
			balance_dict.append({
				"leave_type":lt.name,
				"balance":total_balance
			})

		return balance_dict

	def make_payslips(self):
		if self.status == "Open":
			frappe.throw("Please Close Period Before Creating Payslips")
		else:
			log = frappe.new_doc("Payroll Process Logs")
			log.update({
				"user_id": frappe.session.user, 
				"datetime": frappe.utils.now(), 
				"remarks": "Payroll Period "+ self.name +" Created Payslips",
			})
			if log.insert():
				frappe.db.sql(""" DELETE FROM `tabMy Payslip` WHERE payroll_period = %(period)s """,{ 
						"period": self.name,
					}, as_dict=True)

				leave_type = frappe.db.sql("""SELECT * FROM `tabLeave Type`""",as_dict=True)
				balances = frappe.db.sql(""" SELECT * FROM `tabLB Entry`""", as_dict=True)

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
						
						loan = frappe.db.sql("""SELECT PRE.pay_code, LA.unpaid_amount, LA.total_loan, LA.paid_amount,
						(SELECT COUNT(`name`) FROM `tabLoan Application Payments` WHERE parent = PRE.linked_document and payment_status = 'Paid' and payment_date <= %(pdate)s) as count
						FROM `tabPayroll Register`  PR
						INNER JOIN `tabPayroll Register Entries` PRE ON PRE.parent = PR.`name`
						INNER JOIN `tabLoan Application` LA ON LA.name = PRE.linked_document
		 				WHERE PRE.entry_type = 'Loan' AND PR.period = %(period)s and PR.employee = %(employee)s """,{
							"pdate":self.payroll_date,
							"period": self.name,
							"employee": emp.name,
						}, as_dict=True)

						leaves = self.get_leave_balance(balances,leave_type,emp.name)

						ps = frappe.new_doc("My Payslip")
						ps.update({
							"owner": emp.user_id, "employee": emp.name, "payroll_period": self.name, 
							"employee_name": emp.full_name, "company": emp.company,
							"sss_no": emp.sss_no, "phic_no": emp.phic_no, "hdmf_no": emp.hdmf_no, "tin": emp.tin
						})

						for ln in loan:
							ps.append("loan", {
								"loan_type": ln.pay_code,
								"number_payment": ln.count,
								"paid_amount":ln.paid_amount,
								"loan_amount":ln.total_loan,
								"outstanding_balance":ln.unpaid_amount,
							})

						for lv in leaves:
							if lv['balance'] > 0:
								ps.append("leave", {
									"leave_type": lv['leave_type'],
									"leave_balance": lv['balance'],
								})

						for d in register:
							if d.pay_type == "Income":
								ps.append("payslip_incomes", {
									"description": d.pay_description,
									"amount": d.amount,
									"pay_time": d.pay_time,
								})
							elif d.pay_type == "Deduction":
								ps.append("payslip_deductions", {
									"description": d.pay_description,
									"amount": d.amount,
									"pay_time": d.pay_time,
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
