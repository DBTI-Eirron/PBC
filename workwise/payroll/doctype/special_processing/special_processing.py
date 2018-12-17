# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document

class SpecialProcessing(Document):
	def get_employees(self):
		employees = frappe.db.sql("""SELECT `name`, full_name, location, company, total_yr_days, rate_type, rate, payroll_schedule, min_take_home, cost_center, no_hours, 
			sss_mode, sss_manual, sss_freq, phic_mode, phic_manual, phic_freq, hdmf_mode, hdmf_manual, hdmf_freq, whtax_mode, 
			whtax_manual, whtax_freq, is_attendance_base, ignore_late, on_hold
				FROM tabEmployee
			WHERE company = %(company)s
			AND payroll_schedule = %(pay_sched)s 
			AND is_active = 1 
			AND sensitivity IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
			{conditions}
			ORDER BY last_name, first_name""".format( conditions=self.get_conditions() ),
			({ 
				"company": self.company,
				"pay_sched": self.schedule,
				"employee": self.employee,
				"department": self.department,
			}), as_dict=True)

		return employees

	def get_conditions(self):
		conditions = []
		if self.employee:
			conditions.append("`name`=%(employee)s")

		if self.department:
			conditions.append("department=%(department)s")

		return employees

	def validate_period(self):
		period_stats = frappe.db.get_value("Payroll Period", self.period, "status")
		if period_stats == "Closed":
			frappe.throw(_("Selected Period is Already Closed"))

		if not self.schedule and not self.payroll_date:
			frappe.throw(_("Fill up Mandatory Fields"))
 
	def process_special(self):
		self.validate_period()
		ss_list = []
		entries = []
		header = {
			'transaction_type': "",
			'period': self.period,
			'company': self.company,
			'method': "Standard",
			'rate': 0,
			'remarks': "",
		}

		switcher = {
			"13th Month": self.bonus_pay,
		}

		func = switcher.get(self.method, lambda: frapp.throw(_("Invalid Method")))
		func(header, entries)

		batch = frappe.new_doc("Batch Entry")
		batch.update(header)
		for d in entries:
			if d.get('amount') > 0:
				batch.append("employees", {
					"employee": d.get('employee'),
					"employee_name": d.get('employee_name'),
					"amount": d.get('amount'),
				})

		batch.insert()

		return self.create_log(ss_list)

	def bonus_pay(self, header, entries):
		header['transaction_type'] = frappe.db.get_single_value("Payroll Settings", "bonus_transaction") 
		header['remarks'] = ("13th month pay for year {0}").format(self.payroll_year)

		bonus_method = frappe.db.get_single_value("Payroll Settings", "bonus_method") 
		from_year, to_year = frappe.db.get_value("Payroll Year", self.payroll_year, ["from_date", "to_date"])
		employees = self.get_employees()
		if employees:
			for emp in employees:
				total_bonus = 0
				if bonus_method == "Standard":
					registerx = frappe.db.sql(""" SELECT schedule, bonus, monthly_rate FROM `tabPayroll Register` WHERE employee = %(employee)s 
						AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s AND schedule = %(schedule)s """,{ 
							"employee": emp.name,
							"from_year": from_year,
							"to_year": to_year,
							"schedule": emp.payroll_schedule,
					}, as_dict=True)

					total_rate = 0.0
					months = 0.0
					for d in registerx:
						if d.schedule == "Semi-Monthly":
							months += 0.5
							total_rate = d.monthly_rate
						if d.schedule == "Monthly":
							months += 1
							total_rate = d.monthly_rate

					total_bonus += total_rate * months / 12

				elif bonus_method == "Attendance Base":
					rates = self.get_rates(emp)
					att = frappe.db.sql(""" SELECT bonus, present_days FROM `tabPayroll Register` WHERE employee = %(employee)s AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s """,{ 
						"employee": emp.name,
						"from_year": from_year,
						"to_year": to_year,
					}, as_dict=True)
					present_days = 0
					for d in att:
						present_days += d.present_days

					total_bonus = ( present_days / emp.get('total_yr_days')) * flt(rates.get('monthly_rate'), 8)

				entries.append({
					"employee": emp.name,
					"employee_name": emp.full_name, 
					"amount": total_bonus,
				})

		return header, entries

	def get_rates(self, emp):
		monthly_rate = 0.0
		hourly_rate = 0.0
		semi_rate = 0.0
		daily_rate = 0.0
		if emp['rate'] > 0 and  emp['total_yr_days'] > 0 and emp['no_hours'] > 0:
			month_days = (flt(emp['total_yr_days'], 8) / 12)
			if emp['rate_type'] == "Monthly Rate":
				monthly_rate = flt(emp['rate'], 8)
				semi_rate = flt(emp['rate'], 8) / 2
				daily_rate = flt(emp['rate'], 8) / month_days
				hourly_rate = ( flt(emp['rate'], 8) / month_days ) / emp['no_hours']

			elif emp['rate_type'] == "Hourly Rate":
				monthly_rate = ( flt(emp['rate'], 8) * emp['no_hours'] ) * month_days
				semi_rate = ( flt(emp['rate'], 8) * emp['no_hours'] ) * (month_days / 2)
				daily_rate = flt(emp['rate'], 8) * emp['no_hours']
				hourly_rate = flt(emp['rate'], 8)

			elif emp['rate_type'] == "Daily Rate":
				monthly_rate = flt(emp['rate'], 8) * month_days
				semi_rate = flt(emp['rate'], 8) * (month_days / 2)
				daily_rate = flt(emp['rate'], 8)
				hourly_rate = flt(emp['rate'], 8) / emp['no_hours']

		return {
			"monthly_rate": monthly_rate,
			"semi_rate": semi_rate,
			"daily_rate": daily_rate,
			"hourly_rate": flt(hourly_rate, 8)
		}

	def create_log(self, ss_list):
		log = "<p>" + _("Batch Entries created") + "</p>"
		return log

