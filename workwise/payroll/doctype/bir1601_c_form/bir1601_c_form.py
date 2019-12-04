# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, calendar, time
from frappe.utils import cint, flt, getdate, cstr  
from frappe.model.document import Document
from workwise.payroll.payroll_utils import get_transaction_map
from frappe import _

class BIR1601CForm(Document):
	def validate(self):
		pass
	def compute_value(self):
		self.process_data()

	def get_pay_date(self):
		pay_from = str(self.month)+"-01-"+self.year
		pay_to = str(self.month)+"-"+str(calendar.monthrange(int(self.year), list(calendar.month_abbr).index(self.month[:3]))[1])+"-"+self.year
		pay_from = getdate(str(pay_from))
		pay_to = getdate(str(pay_to))

		return pay_from, pay_to

	def process_data(self):
		if self.company and self.year:
			address_list = frappe.db.sql("""SELECT TA.address_line1, TA.address_line2, TA.city, TA.pincode FROM `tabAddress` TA INNER JOIN `tabDynamic Link` DL ON TA.`name` = DL.parent WHERE DL.link_name = %s""",(self.company),as_dict=True)
			address = ""
			for add in address_list:
				address += cstr(add.address_line1)+", "
				if add.address_line2:
					address += cstr(address_line2)+", "
				address += cstr(add.city)
				self.address = address
				self.zip_code = add.postal_code
			company_info = frappe.db.sql("""SELECT TC.name, TC.tax_id, TC.rdo_code, TC.phone, TC.email FROM `tabCompany` TC WHERE TC.`name` = %s""",(self.company),as_dict=True)		
			for comp in company_info:
				self.tin_number = comp.tax_id
				self.rdo_code = comp.rdo_code
				self.contact_number = comp.phone
				self.email_address = comp.email
	 		pay_from,pay_to = self.get_pay_date()

	 		entries = frappe.db.sql("""
	 			SELECT
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
			WHERE TT.type != 'None' AND
			TE.company = %s AND PR.posting_date BETWEEN %s AND %s
			GROUP BY PRE.`name`""",(self.company,pay_from,pay_to),as_dict=True)
	 		overtime_pay = holiday_pay = trtnt_month_pay = de_minimis = sss_hdmf_phic = wht = statutory = amount_compensation = taxable_salary = 0.00
	 		done = []
	 		for ent in entries:
	 			if ent.name not in done:
		 			amount_compensation += flt(ent.total_income , 8)
		 			taxable_salary += flt(ent.taxable_income , 8)
		 			done.append(ent.name)
				if ent.bir_type == "Overtime" and ent.type == "Income":
					overtime_pay += ent.amount
				if ent.bir_type == "Overtime" and ent.type == "Deduction":
					overtime_pay -= ent.amount
				if ent.bir_type == "Holiday" and ent.type == "Income":
					holiday_pay += ent.amount
				if ent.bir_type == "Holiday" and ent.type == "Deduction":
					holiday_pay -= ent.amount
				if ent.bir_type == "13th Month" and ent.type == "Income":
					trtnt_month_pay += ent.amount
				if ent.bir_type == "13th Month" and ent.type == "Deduction":
					trtnt_month_pay -= ent.amount
				if ent.bir_type == "Deminimis" and ent.type == "Income":
					de_minimis += ent.amount
				if ent.bir_type == "Deminimis" and ent.type == "Deduction":
					de_minimis -= ent.amount
				if ent.pay_code == "SSS":
					sss_hdmf_phic += ent.amount
				if ent.pay_code == "HDMF":
					sss_hdmf_phic += ent.amount
				if ent.pay_code == "PHIC":
					sss_hdmf_phic += ent.amount
				if ent.pay_code == "WHTAX":
					wht += ent.amount
				if ent.daily_rate <= ent.min_wage:
					if ent.bir_type == "Basic" and ent.type == "Income":
						statutory += ent.amount
					if ent.bir_type == "Basic" and ent.type == "Deduction":
						statutory -= ent.amount

			self.total_compensation = amount_compensation
			self.statutory = statutory
			self.overtime = overtime_pay
			self.trtnt_month = trtnt_month_pay
			self.de_minimis = de_minimis
			self.sss = sss_hdmf_phic
			self.total_taxes_withheld = wht

			self.recompute_value()

	def recompute_value(self):
		self.total_non_taxable = flt(self.statutory) + flt(self.other_non_taxable_amount)
		self.total_taxable = flt(self.total_compensation)  - flt(self.total_non_taxable)
		self.net_taxable_compensation = flt(self.total_taxable) - flt(self.less_taxable_compensation)
		self.taxes_withheld_for_remitance = flt(self.total_taxes_withheld) + flt(self.adjustment_of_taxes)
		self.total_tax_remittance = flt(self.less_tax_remitted) + flt(self.other_remittance_amount)
		self.tax_still_due = flt(self.taxes_withheld_for_remitance) - flt(self.total_tax_remittance)
		self.total_penalties = flt(self.surcharge) + flt(self.interest) + flt(self.compromise)
		self.total_amount_still_due = flt(self.tax_still_due) + flt(self.total_penalties)