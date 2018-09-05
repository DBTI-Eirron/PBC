# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document

class BIR2316(Document):
	def validate(self):
		self.get_agent()
	
	def get_agent(self):
		approver = frappe.session.user
		agents = frappe.db.sql("""SELECT full_name FROM tabEmployee WHERE `user_id` = %s LIMIT 1""", (approver), as_dict=True)
		for d in agents:
			self.agent = d.full_name

	def get_info(self):
		emp = frappe.db.sql("""SELECT * FROM tabEmployee WHERE `name` = %(employee)s LIMIT 1""",{ "employee": self.employee,}, as_dict=True)
		for e in emp:
			entry = {
				"tax_id": "000-000-000",
				"rdo_code": "000",
				"employer_name": e.company,
				"civil_status": e.civil_status,
				"birthday": e.birthday,
				"ntax_bs": 0,
				"ntax_ho": 0,
				"ntax_ot": 0,
				"ntax_nd": 0,
				"ntax_bonus": 0,
				"ntax_demi": 0,
				"ntax_contrib": 0,
				"ntax_other": 0,
				"ntax_hazard": 0,
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
			self.date_of_birth = entry.get('birthday')
			self.exemption_status = entry.get('civil_status')
			self.employer_name = entry.get('employer_name')
			self.ntax_bs = entry.get('ntax_bs')
			self.ntax_ho = entry.get('ntax_ho')
			self.ntax_ot = entry.get('ntax_ot')
			self.ntax_nd = entry.get('ntax_nd')
			self.ntax_bonus = entry.get('ntax_bonus')
			self.ntax_demi = entry.get('ntax_demi')
			self.ntax_contrib = entry.get('ntax_contrib')
			self.ntax_other = entry.get('ntax_other')
			self.ntax_hazard = entry.get('ntax_hazard')
			
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
			self.load_tax_id()

		self.get_employee_address()
		self.get_employee_contact()
		self.get_employee_dependants()
		self.get_company_address()

	def get_employee_info(self, e, entry):
		entry['tax_id'] = e.tin
		entry['rdo_code'] = e.rdo_code
		return entry

	def get_company_info(self, e, entry):
		company = frappe.db.sql("""SELECT * FROM tabCompany WHERE `name` = %s LIMIT 1""",(e.company), as_dict=True)
		for d in company:
			entry['employer_name'] = d.name
			entry['employer_addr'] = d.registered_addr

		return entry

	def get_salary_info(self, e, entry, tr_map):
		salary = frappe.db.sql("""SELECT pr.employee, pr.employee_name, pre.pay_code, pre.amount FROM `tabPayroll Register` pr
			INNER JOIN `tabPayroll Register Entries` pre ON pre.parent = pr.`name`
			WHERE employee = %s AND pr.posting_date >= %s AND pr.posting_date <= %s """,(e.name, self.from_date, self.to_date), as_dict=True)

		for d in salary:
			bir_type = tr_map[d.get("pay_code")]['bir_type']
			is_taxable = tr_map[d.get("pay_code")]['is_taxable']

			#TAXABLE
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
				entry['tax_hazard'] += d.amount

			#NON-TAXABLE
			if bir_type == "Basic" and not is_taxable:
				entry['ntax_bs'] += d.amount

			if bir_type == "Holiday" and not is_taxable:
				entry['ntax_ho'] += d.amount

			if bir_type == "Overtime" and not is_taxable:
				entry['ntax_ot'] += d.amount

			if bir_type == "Night Differential" and not is_taxable:
				entry['ntax_nd'] += d.amount

			if bir_type == "13th Month" and not is_taxable:
				entry['ntax_bonus'] += d.amount

			if bir_type == "Deminimis" and not is_taxable:
				entry['ntax_demi'] += d.amount

			if bir_type == "Other" and not is_taxable:
				entry['ntax_other'] += d.amount

			if bir_type == "Hazard" and not is_taxable:
				entry['ntax_hazard'] += d.amount
			
			if bir_type == "Contribution":
				entry['ntax_contrib'] += d.amount

		if is_taxable:
			entry['tax_total'] = entry['tax_bs'] + entry['tax_rep'] + entry['tax_transpo'] + entry['tax_cola'] + entry['tax_housing'] + entry['tax_commission'] + entry['tax_sharing'] + entry['tax_fees'] + entry['tax_bonus'] + entry['tax_ot'] + entry['tax_hazard']
			
			entry['ntax_total'] = entry['ntax_bs'] + entry['ntax_ho'] + entry['ntax_ot'] + entry['ntax_nd'] + entry['ntax_bonus'] + entry['ntax_demi'] + entry['ntax_contrib'] + entry['ntax_other']

		return entry

	def get_transaction_map(self):
		tr_map = {}
		tr = frappe.db.sql("""SELECT code, title, type, entry_type, account, bir_type, is_taxable, is_bonus, is_government, is_standard, is_active FROM `tabTransaction Type` """, as_dict=1)
		for t in tr:
			tr_map[t.code] = {"code": t.code, "title": t.title, "type": t.type, "entry_type": t.entry_type,	"account": t.account, "bir_type": t.bir_type, 
				"is_taxable": t.is_taxable, "is_standard": t.is_standard, "is_active": t.is_active, "is_bonus": t.is_bonus, "is_government": t.is_government,
			}
		return tr_map

	def load_dates(self):
		from_date, to_date = frappe.db.get_value("Payroll Year",self.payroll_year,["from_date", "to_date"])
		if from_date and to_date:
			self.from_date = from_date
			self.to_date = to_date

	def load_tax_id(self):
		tax_id = self.tax_id.replace("-","")
		if len(tax_id) <= 9:
			tax_id = tax_id + "0000"
		tl = tax_id[:-10]
		tm = tax_id[3:-7]
		tr = tax_id[6:-4]
		tx = tax_id[9:]
		self.tax_id = tl+"-"+tm+"-"+tr+"-"+tx

	def get_employee_address(self):
		employee_address = frappe.db.sql(""" SELECT DISTINCT TA.`address_line1`, TA.`pincode`, TA.`address_type` FROM `tabDynamic Link` DL JOIN `tabAddress` TA WHERE DL.`parenttype` = "Address" AND DL.`link_doctype` = "Employee" AND DL.`parent` = TA.`name` AND TA.`address_type` = "Foreign" OR TA.`address_type` = "Local Home" OR TA.`address_type` = "Registered" AND DL.`link_name` = %s """, (self.employee), as_dict=1)
		for add in employee_address:
			if add.address_type == "Foreign":
				self.foreign_address = add.address_line1
				self.foreign_address_zipcode = add.pincode
			if add.address_type == "Registered":
				self.registered_address = add.address_line1
				self.registered_address_zipcode = add.pincode
			if add.address_type == "Local Home":
				self.local_address = add.address_line1
				self.local_address_zipcode = add.pincode

	def get_employee_contact(self):
		employee_contact = frappe.db.sql(""" SELECT DISTINCT TC.`phone` FROM `tabContact` TC JOIN `tabDynamic Link` DL WHERE DL.`parenttype` = "Contact" AND DL.`link_doctype` = "Employee" AND DL.`link_name` = %s LIMIT 1""", (self.employee), as_dict=1)
		for con in employee_contact:
			self.telephone_number = con.phone

	def get_employee_dependants(self):
		i = 1
		employee_family = frappe.db.sql(""" SELECT DISTINCT `full_name`, `birthday` FROM `tabFamily Members` WHERE `is_qualified_dependent` = 1 AND `parent` = %s """, (self.employee), as_dict=1)
		for d in employee_family:
			if i == 1:
				self.dependent_name_1 = d.full_name
				self.dependent_birthday_1 = d.birthday
			if i == 2:
				self.dependent_name_2 = d.full_name
				self.dependent_birthday_2 = d.birthday
			if i == 3:
				self.dependent_name_3 = d.full_name
				self.dependent_birthday_3 = d.birthday
			if i == 4:
				self.dependent_name_4 = d.full_name
				self.dependent_birthday_4 = d.birthday
			if i >=5:
				break
			i += 1

	def get_company_address(self):
		company_address = frappe.db.sql(""" SELECT DISTINCT TA.`address_line1`, TA.`pincode`, TA.`address_type` FROM `tabDynamic Link` DL JOIN `tabAddress` TA WHERE DL.`parenttype` = "Address" AND DL.`link_doctype` = "Company" AND DL.`parent` = TA.`name` AND TA.`address_type` = "Registered" AND DL.`link_name` = %s """, (self.employer_name), as_dict=1)
		for com in company_address:
			self.employer_addr = com.address_line1
			self.employer_zip = com.pincode