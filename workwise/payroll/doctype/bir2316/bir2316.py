# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document

class BIR2316(Document):
	def get_info(self):
		emp = frappe.db.sql("""SELECT * FROM tabEmployee WHERE `name` = %(employee)s LIMIT 1""",{ "employee": self.employee,}, as_dict=True)
		for e in emp:
			entry = {
				"tax_id": "000-000-000",
				"rdo_code": "000",
				"exemption_status": "",
				"employer_name": "",
				"employer_addr": "",
				"ntax_bs": 0,
				"ntax_ho": 0,
				"ntax_ot": 0,
				"ntax_nd": 0,
				"ntax_bonus": 0,
				"ntax_demi": 0,
				"ntax_contrib": 0,
				"ntax_other": 0,
				"tax_bs": 0,
				"tax_rep": 0,
				"tax_transpo": 0,
				"tax_cola": 0,
				"tax_housing": 0,
				"tax_commission": 0,
				"tax_sharing": 0,
				"tax_fees": 0,
				"tax_bonus": 0,
				"tax_ot": 0,
				"tax_hazard": 0,	
				"ntax_total": 0,
				"tax_total": 0,
			}

			tr_map = self.get_transaction_map()
			self.get_employee_info(e, entry)
			self.get_company_info(e, entry)
			self.get_salary_info(e, entry, tr_map)
			
			self.tax_id = entry.get('tax_id')
			self.rdo_code = entry.get('rdo_code')
			self.exemption_status = entry.get('exemption_status')
			self.employer_name = entry.get('employer_name')
			self.employer_addr = entry.get('employer_addr')
			self.ntax_bs = entry.get('ntax_bs')
			self.ntax_ho = entry.get('ntax_ho')
			self.ntax_ot = entry.get('ntax_ot')
			self.ntax_nd = entry.get('ntax_nd')
			self.ntax_bonus = entry.get('ntax_bonus')
			self.ntax_demi = entry.get('ntax_demi')
			self.ntax_contrib = entry.get('ntax_contrib')
			self.ntax_other = entry.get('ntax_other')
			
			self.tax_bs = entry.get('tax_bs')
			self.tax_rep = entry.get('tax_rep')
			self.tax_transpo = entry.get('tax_transpo')
			self.tax_cola = entry.get('tax_cola')
			self.tax_housing = entry.get('tax_housing')
			self.tax_commission = entry.get('tax_commission')
			self.tax_sharing = entry.get('tax_sharing')
			self.tax_fees = entry.get('tax_fees')
			self.tax_bonus = entry.get('tax_bonus')
			self.tax_ot = entry.get('tax_ot')
			self.tax_hazard = entry.get('tax_hazard')
			self.ntax_total = entry.get('ntax_total')
			self.tax_total = entry.get('tax_total')

	def get_employee_info(self, e, entry):
		entry['tax_id'] = e.tin
		entry['tax_id'] = e.tin
		return entry

	def get_company_info(self, e, entry):
		company = frappe.db.sql("""SELECT * FROM tabCompany WHERE `name` = %s LIMIT 1""",(e.company), as_dict=True)
		for d in company:
			entry['employer_name'] = d.name

		return entry

	def get_salary_info(self, e, entry, tr_map):
		salary = frappe.db.sql("""SELECT pr.employee, pr.employee_name, pre.pay_code, pre.amount FROM `tabPayroll Register` pr
			INNER JOIN `tabPayroll Register Entries` pre ON pre.parent = pr.`name`
			WHERE employee = %s AND pr.posting_date >= %s AND pr.posting_date <= %s """,(e.name, self.from_date, self.to_date), as_dict=True)
		
		for d in salary:
			bir_type = tr_map[d.get("pay_code")]['bir_type']
			is_taxable = tr_map[d.get("pay_code")]['is_taxable']

			if bir_type == "Basic" and is_taxable:
				entry['tax_bs'] += d.amount

			if bir_type == "Representation" and is_taxable:
				entry['tax_rep'] += d.amount

			if bir_type == "Transportation" and is_taxable:
				entry['tax_transpo'] += d.amount

			if bir_type == "COLA" and is_taxable:
				entry['tax_cola'] += d.amount

			if bir_type == "Housing Allowance" and is_taxable:
				entry['tax_housing'] += d.amount

			if bir_type == "Commission" and is_taxable:
				entry['tax_commission'] += d.amount

			if bir_type == "Profit Sharing" and is_taxable:
				entry['tax_sharing'] += d.amount

			if bir_type == "Fees" and is_taxable:
				entry['tax_fees'] += d.amount

			if bir_type == "13 Month" and is_taxable:
				entry['tax_bonus'] += d.amount

			if bir_type == "Overtime" and is_taxable:
				entry['tax_ot'] += d.amount

			if bir_type == "Hazard" and is_taxable:
				entry['tax_ot'] += d.amount

		return entry

	def get_transaction_map(self):
		tr_map = {}
		tr = frappe.db.sql("""SELECT code, title, type, entry_type, account, bir_type, is_taxable, is_bonus, is_government, is_standard, is_active FROM `tabTransaction Type` """, as_dict=1)
		for t in tr:
			tr_map[t.code] = {"code": t.code, "title": t.title, "type": t.type, "entry_type": t.entry_type,	"account": t.account, "bir_type": t.bir_type, 
				"is_taxable": t.is_taxable, "is_standard": t.is_standard, "is_active": t.is_active, "is_bonus": t.is_bonus, "is_government": t.is_government,
			}
		return tr_map
