# -*- coding: utf-8 -*-
# Copyright (c) 2023, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from workwise.payroll.payroll_utils import format_precision	

class BIR1601cForm(Document):
	def update_data(self):
		if self.company and self.month and self.month:
			entries = frappe.db.sql("""SELECT
				PR.`name`,
				PRE.amount,
				PRE.pay_code,
				PR.daily_rate,
				PR.total_income,
				PR.taxable_income,
				TT.type,
				TT.bir_type,
				TL.min_wage
			FROM `tabPayroll Register Entries` PRE
			INNER JOIN `tabPayroll Register` PR ON PRE.parent = PR.name
			INNER JOIN `tabTransaction Type` TT ON PRE.pay_code = TT.`code`
			INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
			INNER JOIN `tabLocation` TL ON TE.location = TL.`name`
			INNER JOIN `tabPayroll Period` PP ON PR.period = PP.name
			WHERE PR.company = %(company)s
			AND PP.payroll_year = %(payroll_year)s
			AND PP.payroll_month = %(payroll_month)s
			GROUP BY PRE.`name`""",{ 
			"company": self.company,
			"payroll_year": self.year,
			"payroll_month": self.month,
			}, as_dict=True)
			overtime_pay = holiday_pay = trtnt_month_pay = de_minimis = contribution = mwe_contribution = wht = statutory = basic = other = night_dif = 0.00
			done = []
			for ent in entries:
				# if ent.name not in done:
				# 	amount_compensation += flt(ent.total_income , 8)
				# 	taxable_salary += flt(ent.taxable_income , 8)
				# 	done.append(ent.name)
				if ent.bir_type == "Basic":
					basic += ent.amount if ent.type == "Income" else -(ent.amount)

				#WHT
				if ent.bir_type == "TAX":
					wht += -(ent.amount) if ent.type == "Income" else ent.amount
				
				#13th Month
				if ent.bir_type == "13th Month":
					trtnt_month_pay += ent.amount if ent.type == "Income" else -(ent.amount)

				#Deminimis
				if ent.bir_type == "Deminimis":
					de_minimis += ent.amount if ent.type == "Income" else -(ent.amount)

				if ent.bir_type == "Leave Conversion":
					de_minimis += ent.amount if ent.type == "Income" else -(ent.amount)

				# if ent.bir_type == "Medical Cash Allowance":
				# 	de_minimis += ent.amount if ent.type == "Income" else -(ent.amount)

				if ent.bir_type == "Rice Subsidy":
					de_minimis += ent.amount if ent.type == "Income" else -(ent.amount)

				if ent.bir_type == "Uniform":
					de_minimis += ent.amount if ent.type == "Income" else -(ent.amount)

				if ent.bir_type == "Actual Medical Assistance":
					de_minimis += ent.amount if ent.type == "Income" else -(ent.amount)

				if ent.bir_type == "Laundry Allowance":
					de_minimis += ent.amount if ent.type == "Income" else -(ent.amount)

				# if ent.bir_type == "Achievement Awards":
				# 	de_minimis += ent.amount if ent.type == "Income" else -(ent.amount)

				# if ent.bir_type == "Gifts":
				# 	de_minimis += ent.amount if ent.type == "Income" else -(ent.amount)

				if ent.bir_type == "Productivity Incentive":
					de_minimis += ent.amount if ent.type == "Income" else -(ent.amount)

				#Others
				if ent.bir_type == "Other" and ent.type == "Income":
					other += ent.amount
				if ent.bir_type == "Other" and ent.type == "Deduction":
					other -= ent.amount

				#Contribution
				if ent.bir_type == "Contribution":
					contribution += -(ent.amount) if ent.type == "Income" else ent.amount

				#MWE
				if ent.daily_rate <= ent.min_wage:
					if ent.bir_type == "Basic":
						statutory += ent.amount if ent.type == "Income" else -(ent.amount)

					#Contribution
					if ent.bir_type == "Contribution":
						mwe_contribution += -(ent.amount) if ent.type == "Income" else ent.amount

					#Holiday
					if ent.bir_type == "Overtime":
						holiday_pay += ent.amount if ent.type == "Income" else -(ent.amount)
					if ent.bir_type == "Holiday":
						holiday_pay += ent.amount if ent.type == "Income" else -(ent.amount)
					if ent.bir_type == "Night Differential":
						holiday_pay += ent.amount if ent.type == "Income" else -(ent.amount)
					if ent.bir_type == "Hazard":
						holiday_pay += ent.amount if ent.type == "Income" else -(ent.amount)


			self.total_compensation = format_precision(basic+holiday_pay+de_minimis+trtnt_month_pay,2)
			self.statutory = format_precision(statutory-mwe_contribution,2)
			self.overtime = format_precision(flt(holiday_pay,8),2)
			self.trtnt_month = format_precision(trtnt_month_pay,2)
			self.de_minimis = format_precision(de_minimis,2)
			self.sss = format_precision(contribution,2)
			self.other_non_taxable_amount = format_precision(other,2)
			self.less_taxable_compensation = format_precision(0,2)
			self.total_taxes_withheld = format_precision(wht,2)
			self.adjustment_of_taxes = format_precision(0,2)
				
	def update_totals(self):
		self.total_non_taxable = self.statutory + self.overtime + self.trtnt_month + self.de_minimis + self.sss + self.other_non_taxable_amount
		self.total_taxable = self.total_compensation - self.total_non_taxable
		self.taxes_withheld_for_remitance = self.total_taxes_withheld + self.adjustment_of_taxes
		self.net_taxable_compensation = self.total_taxable - self.less_taxable_compensation
		self.total_tax_remittance = self.other_remittance_amount + self.less_tax_remitted
		self.tax_still_due = self.taxes_withheld_for_remitance - self.total_tax_remittance
		self.total_penalties = self.surcharge + self.interest + self.compromise
		self.total_amount_still_due = self.tax_still_due + self.total_penalties