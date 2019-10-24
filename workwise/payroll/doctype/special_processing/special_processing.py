# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document
from workwise.payroll.annualization import create_annualization
from workwise.payroll.payroll_utils import get_rates
from workwise.payroll.payroll_utils import get_transaction_map
from workwise.time_keeping.application_utils import validate_inactive_employee

class SpecialProcessing(Document):
	def get_employees(self):
		employees = frappe.db.sql("""SELECT TE.`name`, TE.full_name, TE.location, TE.company, TE.total_yr_days, 
			TE.rate_type, TE.rate, TE.payroll_schedule, TE.min_take_home, TE.cost_center, TE.no_hours, TE.sss_mode, TE.sss_manual, 
			TE.sss_freq, TE.phic_mode, TE.phic_manual, TE.phic_freq, TE.hdmf_mode, TE.hdmf_manual, TE.hdmf_freq, TE.whtax_mode, 
			TE.whtax_manual, TE.whtax_freq, TE.is_attendance_base, TE.ignore_late, TE.on_hold
			FROM `tabEmployee` TE INNER JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name`
			WHERE TE.company = %(company)s
			AND TE.payroll_schedule = %(pay_sched)s 
			AND TE.is_active = 1 
			{conditions}
			ORDER BY TE.last_name, TE.first_name""".format( conditions=self.get_conditions() ),
			({ 
				"company": self.company,
				"pay_sched": self.schedule,
				"employee": self.employee,
				"department": self.department,
				"location": self.location,
			}), as_dict=True)

		return employees

	def get_conditions(self):
		conditions = []
		if frappe.session.user != "Administrator":
			conditions.append(_("TE.sensitivity IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

		if self.employee:
			conditions.append("TE.`name`=%(employee)s")

		if self.department:
			lft, rgt = frappe.db.get_value("Department", self.department, ["lft", "rgt"])
			conditions.append(_("( DEPT.`lft` BETWEEN '{0}' AND '{1}' )").format(lft, rgt))

		if self.location:
			conditions.append("TE.location=%(location)s")

		return "AND {}".format(" AND ".join(conditions)) if conditions else ""

	def validate_period(self):
		period_stats = frappe.db.get_value("Payroll Period", self.period, "status")
		if period_stats == "Closed":
			frappe.throw(_("Selected Period is Already Closed"))

		if not self.schedule and not self.payroll_date:
			frappe.throw(_("Fill up Mandatory Fields"))
 
	def process_special(self):
		if self.employee:
			validate_inactive_employee(self)
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
			"Leave Balance to Cash": self.leave_to_cash,
			"Annualization": self.annualization,
		}

		func = switcher.get(self.method, lambda: frapp.throw(_("Invalid Method")))
		func(header, entries)

		if self.method != "Annualization":
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
					registerx = frappe.db.sql(""" SELECT PRE.`name`, PRE.`pay_code`, PRE.`amount`
						FROM `tabPayroll Register Entries` PRE 
						INNER JOIN `tabPayroll Register` PR ON PRE.`parent`=PR.`name`
						WHERE PRE.`pay_code` = 'BS' AND PR.`employee` = %(employee)s 
						AND PR.`posting_date` >= %(from_year)s AND PR.`posting_date` <= %(to_year)s """,{ 
						"employee": emp.name,
						"from_year": from_year,
						"to_year": to_year,
					}, as_dict=True)

					for d in registerx:
						if d.pay_code == 'BS':
							total_bonus += d.amount

					total_bonus = total_bonus / 12

				elif bonus_method == "Bonus Basis":
					bonus_basis = frappe.db.sql(""" SELECT bonus FROM `tabPayroll Register` WHERE employee = %(employee)s 
						AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s """,{ 
							"employee": emp.name,
							"from_year": from_year,
							"to_year": to_year,
					}, as_dict=True)

					for d in bonus_basis:
						total_bonus += d.bonus

					total_bonus = total_bonus / 12

				elif bonus_method == "Attendance Base":
					#rates = self.get_rates(emp)
					#att = frappe.db.sql(""" SELECT bonus, present_days FROM `tabPayroll Register` WHERE employee = %(employee)s AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s """,{ 
					#	"employee": emp.name,
					#	"from_year": from_year,
					#	"to_year": to_year,
					#}, as_dict=True)

					#present_days = 0
					#for d in att:
					#	present_days += d.present_days

					#total_bonus = ( present_days / emp.get('total_yr_days')) * flt(rates.get('monthly_rate'), 8)

					att = frappe.db.sql(""" SELECT PRE.`name`, PRE.`pay_code`, PRE.`amount`, TT.`entry_type`, TT.`type` 
						FROM `tabPayroll Register Entries` PRE 
						INNER JOIN `tabPayroll Register` PR ON PRE.`parent`=PR.`name`
						INNER JOIN `tabTransaction Type` TT ON PRE.`pay_code`=TT.`name` 
						WHERE PR.`employee` = %(employee)s AND PR.`posting_date` >= %(from_year)s AND PR.`posting_date` <= %(to_year)s """,{ 
						"employee": emp.name,
						"from_year": from_year,
						"to_year": to_year,
					}, as_dict=True)

					for d in att:
						if d.pay_code == 'BS':
							total_bonus += d.amount

						if d.entry_type == 'Attendance':
							if d.type == 'Income':
								total_bonus += d.amount
							if d.type == 'Deduction':
								total_bonus -= d.amount

					total_bonus = total_bonus / 12

				entries.append({
					"employee": emp.name,
					"employee_name": emp.full_name, 
					"amount": total_bonus,
				})

		return header, entries

	def leave_to_cash(self, header, entries):
		header['transaction_type'] = frappe.db.get_single_value("Payroll Settings", "tr_leave_to_cash") 
		header['remarks'] = ("Leave to cash for year {0}").format(self.payroll_year)

		bonus_method = frappe.db.get_single_value("Payroll Settings", "bonus_method") 
		from_year, to_year = frappe.db.get_value("Payroll Year", self.payroll_year, ["from_date", "to_date"])
		employees = self.get_employees()
		if employees:
			for emp in employees:
				total_bonus = 0
	
				registerx = frappe.db.sql(""" SELECT credits, used_credits `tabLeave Balance` WHERE employee = %(employee)s 
					AND from_date >= %(from_year)s AND to_date <= %(to_year)s AND schedule = %(schedule)s """,{ 
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

				entries.append({
					"employee": emp.name,
					"employee_name": emp.full_name, 
					"amount": total_bonus,
				})

		return header, entries

	def annualization(self, header, entries):
		log = "Created Annualization Entries"
		create_annualization(self)
		return log

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
		log = "<p>" + _("Special Entries created") + "</p>"
		return log

