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
		if self.document_type == "Current":
			self.get_info()
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
				"employee": e.name,
				"employee_name": e.employee_name,
				"tax_id": "000-000-000",
				"rdo_code": "000",
				"prev_from_date": "",

				"tax_id": "",
				"local_address": "",
				"registered_address": "",
				"foreign_address": "",
				"date_of_birth": "",
				"exemption_status": "",
				"rdo_code": "",
				"local_address_zipcode": "",
				"registered_address_zipcode": "",
				"foreign_address_zipcode": "",
				"telephone_number": "",

				"dependent_name_1": "",
				"dependent_birthday_1": "",
				"dependent_name_3": "",
				"dependent_birthday_3": "",
				"dependent_name_2": "",
				"dependent_birthday_2": "",
				"dependent_name_4": "",
				"dependent_birthday_4": "",

				"employer_tax_id": "000-000-000",
				"employer_name": "",
				"employer_addr": "",
				"employer_zip": "",

				"prev_employer_tax_id": "000-000-000",
				"prev_employ_name": "",
				"prev_employ_addr": "",
				"prev_employ_zip": "",

				"sum_gcipe": 0.0,
				"sum_tnt": 0.0,
				"sum_tci": 0.0,
				"sum_tcipe": 0.0,
				"sum_gtci": 0.0,
				"sum_te": 0.0,
				"sum_pph": 0.0,
				"sum_ntci": 0.0,
				"sum_td": 0.0,
				"sum_atw_pres": 0.0,
				"sum_atw_prev": 0.0,
				"sum_tatwa": 0.0,

				"ntax_bs": 0.0,
				"ntax_ho": 0.0,
				"ntax_ot": 0.0,
				"ntax_nd": 0.0,
				"ntax_bonus": 0.0,
				"ntax_demi": 0.0,
				"ntax_contrib": 0.0,
				"ntax_other": 0.0,
				"ntax_hazard": 0.0,

				"tax_bs": 0.0,
				"tax_rep": 0.0,
				"tax_transpo": 0.0,
				"tax_cola": 0.0,
				"tax_housing": 0.0,
				"tax_commission": 0.0,
				"tax_sharing": 0.0,
				"tax_fees": 0.0,
				"tax_bonus": 0.0,
				"tax_ot": 0.0,
				"tax_hazard": 0.0,

				"ntax_total": 0.0,
				"tax_total": 0.0,
			}

			self.set_employee_information(e, entry)
			self.set_qualified_dependent_children(e, entry)
			self.set_employer_information_present(e, entry)
			self.set_employer_information_previous(e, entry)
			self.set_computations(e, entry)
			self.set_summary(e, entry)

			self.load_tax_id(e, entry)
			self.load_employer_pres_tax_id(e, entry)
			self.load_employer_prev_tax_id(e, entry)

	def set_employee_information(self, e, entry):	
		self.get_employee_info(e, entry)
		self.get_employee_address(e, entry)
		self.get_employee_contact(e, entry)

		self.tax_id = entry.get('tax_id')
		self.local_address = entry.get('local_address')
		self.registered_address = entry.get('registered_address')
		self.foreign_address = entry.get('foreign_address')
		self.date_of_birth = entry.get('date_of_birth')
		self.exemption_status = entry.get('exemption_status')
		self.rdo_code = entry.get('rdo_code')
		self.local_address_zipcode = entry.get('local_address_zipcode')
		self.registered_address_zipcode = entry.get('registered_address_zipcode')
		self.foreign_address_zipcode = entry.get('foreign_address_zipcode')
		self.telephone_number = entry.get('telephone_number')

	def set_qualified_dependent_children(self, e, entry):
		self.get_employee_dependants(e, entry)

		self.dependent_name_1 = entry.get('dependent_name_1')
		self.dependent_birthday_1 = entry.get('dependent_birthday_1')
		self.dependent_name_3 = entry.get('dependent_name_3')
		self.dependent_birthday_3 = entry.get('dependent_birthday_3')
		self.dependent_name_2 = entry.get('dependent_name_2')
		self.dependent_birthday_2 = entry.get('dependent_birthday_2')
		self.dependent_name_4 = entry.get('dependent_name_4')
		self.dependent_birthday_4 = entry.get('dependent_birthday_4')

	def set_employer_information_present(self, e, entry):
		self.get_company_info(e, entry)
		self.get_company_address(e, entry)

		self.employer_tax_id = entry.get('employer_tax_id')
		self.employer_name = entry.get('employer_name')
		self.employer_addr = entry.get('employer_addr')
		self.employer_zip = entry.get('employer_zip')

	def set_employer_information_previous(self, e, entry):
		self.get_prev_employer_info(e, entry)

		self.prev_employer_tax_id = entry.get('prev_employer_tax_id')
		self.prev_employ_name = entry.get('prev_employ_name')
		self.prev_employ_addr = entry.get('prev_employ_addr')
		self.prev_employ_zip = entry.get('prev_employ_zip')

	def set_summary(self, e, entry):
		self.get_summary_info(e, entry)
		self.get_whtax_info(e, entry)

		self.sum_gcipe = entry.get('ntax_total') + entry.get('tax_total')
		self.sum_tnt = entry.get('ntax_total')
		self.sum_tci = entry.get('tax_total')
		self.sum_tcipe = entry.get('sum_tcipe')
		self.sum_gtci = entry.get('sum_gtci')
		self.sum_te = entry.get('sum_te')
		self.sum_pph = entry.get('sum_pph')
		self.sum_ntci = entry.get('sum_gtci') - entry.get('sum_te') - entry.get('sum_pph')
		self.sum_atw_pres = entry.get('sum_atw_pres')
		self.sum_atw_prev = entry.get('sum_atw_prev')
		self.sum_tatwa = entry.get('sum_atw_pres') + flt(self.sum_atw_prev, 2)

	def set_computations(self, e, entry):
		tr_map = self.get_transaction_map()
		self.get_salary_info(e, entry, tr_map)
		self.get_monthpay_info(e, entry)
		self.get_monthpay_ceiling_info(e, entry)

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

	def load_tax_id(self, e, entry):
		if self.tax_id:
			tax_id = self.tax_id.replace("-","")
			if len(tax_id) <= 9:
				tax_id = tax_id + "0000"
			tl = tax_id[:-10]
			tm = tax_id[3:-7]
			tr = tax_id[6:-4]
			tx = tax_id[9:]
			self.tax_id = tl+"-"+tm+"-"+tr+"-"+tx

		return entry

	def load_employer_pres_tax_id(self, e, entry):
		if self.employer_tax_id:
			tax_id = self.employer_tax_id.replace("-","")
			if len(tax_id) <= 9:
				tax_id = tax_id + "0000"
			tl = tax_id[:-10]
			tm = tax_id[3:-7]
			tr = tax_id[6:-4]
			tx = tax_id[9:]
			self.employer_tax_id = tl+"-"+tm+"-"+tr+"-"+tx

		return entry

	def load_employer_prev_tax_id(self, e, entry):
		if self.prev_employer_tax_id:
			tax_id = self.prev_employer_tax_id.replace("-","")
			if len(tax_id) <= 9:
				tax_id = tax_id + "0000"
			tl = tax_id[:-10]
			tm = tax_id[3:-7]
			tr = tax_id[6:-4]
			tx = tax_id[9:]
			self.prev_employer_tax_id = tl+"-"+tm+"-"+tr+"-"+tx

		return entry

	def get_employee_info(self, e, entry):
		entry['tax_id'] = e.tin
		entry['rdo_code'] = e.rdo_code
		entry['exemption_status'] = e.civil_status
		entry['date_of_birth'] = e.birthday

		return entry

	def get_employee_address(self, e, entry):
		employee_address = frappe.db.sql(""" SELECT DISTINCT TA.`address_line1`, TA.`pincode`, TA.`address_type` FROM `tabDynamic Link` DL JOIN `tabAddress` TA ON DL.`parent`=TA.`name` WHERE DL.`parenttype` = "Address" AND DL.`link_doctype` = "Employee" AND DL.`parent` = TA.`name` AND TA.`address_type` = "Foreign" OR TA.`address_type` = "Local Home" OR TA.`address_type` = "Registered" AND DL.`link_name` = %s """, (self.employee), as_dict=1)
		for add in employee_address:
			if add.address_type == "Foreign":
				entry['foreign_address'] = add.address_line1
				entry['foreign_address_zipcode'] = add.pincode
			if add.address_type == "Registered":
				entry['registered_address'] = add.address_line1
				entry['registered_address_zipcode'] = add.pincode
			if add.address_type == "Local Home":
				entry['local_address'] = add.address_line1
				entry['local_address_zipcode'] = add.pincode

		return entry

	def get_employee_contact(self, e, entry):
		employee_contact = frappe.db.sql(""" SELECT DISTINCT TC.`phone` FROM `tabContact` TC JOIN `tabDynamic Link` DL WHERE DL.`parenttype` = "Contact" AND DL.`link_doctype` = "Employee" AND DL.`link_name` = %s LIMIT 1""", (self.employee), as_dict=1)
		for con in employee_contact:
			entry['telephone_number'] = con.phone

		return entry

	def get_employee_dependants(self, e, entry):
		i = 1
		employee_family = frappe.db.sql(""" SELECT DISTINCT `full_name`, `birthday` FROM `tabFamily Members` WHERE `is_qualified_dependent` = 1 AND `parent` = %s """, (self.employee), as_dict=1)
		for d in employee_family:
			if i == 1:
				entry['dependent_name_1'] = d.full_name
				entry['dependent_birthday_1'] = d.birthday
			if i == 2:
				entry['dependent_name_2'] = d.full_name
				entry['dependent_birthday_2'] = d.birthday
			if i == 3:
				entry['dependent_name_3'] = d.full_name
				entry['dependent_birthday_3'] = d.birthday
			if i == 4:
				entry['dependent_name_4'] = d.full_name
				entry['dependent_birthday_4'] = d.birthday
			if i >=5:
				break
			i += 1

		return entry

	def get_company_info(self, e, entry):
		company = frappe.db.sql("""SELECT * FROM tabCompany WHERE `name` = %s LIMIT 1""",(e.company), as_dict=True)
		for d in company:
			entry['employer_name'] = d.name
			entry['employer_tax_id'] = d.tax_id

		return entry

	def get_company_address(self, e, entry):
		company_address = frappe.db.sql(""" SELECT DISTINCT TA.`address_line1`, TA.`pincode`, TA.`address_type` FROM `tabDynamic Link` DL JOIN `tabAddress` TA WHERE DL.`parenttype` = "Address" AND DL.`link_doctype` = "Company" AND DL.`parent` = TA.`name` AND TA.`address_type` = "Registered" AND DL.`link_name` = %s """, (e.company), as_dict=1)
		for com in company_address:
			entry['employer_addr'] = com.address_line1
			entry['employer_zip'] = com.pincode

		return entry

	def get_prev_employer_info(self, e, entry):
		prev_bir = frappe.db.sql(""" SELECT DISTINCT * FROM `tabBIR2316` WHERE document_type = "Previous" AND `employee` = %s AND docstatus = 1 LIMIT 1 """, (self.employee), as_dict=1)

		if prev_bir:
			for d in prev_bir:
				entry['prev_employer_tax_id'] = d.prev_employer_tax_id
				entry['prev_employ_name'] = d.prev_employ_name
				entry['prev_employ_addr'] = d.prev_employ_addr
				entry['prev_employ_zip'] = d.prev_employ_zip
				entry['prev_from_date'] = d.from_date
				entry['sum_tcipe'] += d.sum_tcipe
				entry['sum_atw_prev'] += d.sum_atw_prev

		return entry

	def get_summary_info(self, e, entry):
		summary = frappe.db.sql("""SELECT DISTINCT employee, employee_name, gross_payroll, taxable_income FROM `tabPayroll Register`
			WHERE employee = %s AND posting_date >= %s AND posting_date <= %s """,(e.name, getdate(self.from_date), getdate(self.to_date)), as_dict=True)

		if summary:
			for d in summary:
				entry['sum_gtci'] += d.gross_payroll
				entry['sum_td'] += d.taxable_income

		return entry

	def get_whtax_info(self, e, entry):
		salary = frappe.db.sql("""SELECT DISTINCT pr.employee, pr.employee_name, pre.pay_code, pre.amount FROM `tabPayroll Register` pr
			INNER JOIN `tabPayroll Register Entries` pre ON pre.parent = pr.`name`
			WHERE employee = %s AND pr.posting_date >= %s AND pr.posting_date <= %s """,(e.name, self.from_date, self.to_date), as_dict=True)

		for d in salary:
			if d.pay_code == "WHTAX":
				entry['sum_atw_pres'] += d.amount

		return entry

	def get_transaction_map(self):
		tr_map = {}
		tr = frappe.db.sql("""SELECT code, title, type, entry_type, account, bir_type, is_taxable, is_bonus, is_government, is_standard, is_active FROM `tabTransaction Type` """, as_dict=1)
		for t in tr:
			tr_map[t.code] = {"code": t.code, "title": t.title, "type": t.type, "entry_type": t.entry_type,	"account": t.account, "bir_type": t.bir_type, 
				"is_taxable": t.is_taxable, "is_standard": t.is_standard, "is_active": t.is_active, "is_bonus": t.is_bonus, "is_government": t.is_government,
			}
		return tr_map

	def get_salary_info(self, e, entry, tr_map):
		bir_type = ""
		is_taxable = ""
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

		#if is_taxable:
			entry['tax_total'] = entry['tax_bs'] + entry['tax_rep'] + entry['tax_transpo'] + entry['tax_cola'] + entry['tax_housing'] + entry['tax_commission'] + entry['tax_sharing'] + entry['tax_fees'] + entry['tax_bonus'] + entry['tax_ot'] + entry['tax_hazard']
			
			entry['ntax_total'] = entry['ntax_bs'] + entry['ntax_ho'] + entry['ntax_ot'] + entry['ntax_nd'] + entry['ntax_bonus'] + entry['ntax_demi'] + entry['ntax_contrib'] + entry['ntax_other']

		return entry

	def get_monthpay_info(self, e, entry):
		monthpay = frappe.db.sql("""SELECT DISTINCT LP.`amount` FROM `tabLast Pay Register` LP JOIN `tabLast Pay Entry` LE ON LP.`parent`=LE.`name` WHERE LP.`description` = "Pro Rated 13th Month" AND LE.`employee` = %s AND LE.posting_date >= %s AND LE.posting_date <= %s """,(e.name, self.from_date, self.to_date), as_dict=True)

		for d in monthpay:
			entry['ntax_bonus'] += d.amount

		entry['ntax_total'] += entry['ntax_bonus']
		
		return entry

	def get_monthpay_ceiling_info(self, e, entry):
		ceiling_limit = 0.0
		total_bonus = 0.0
		prev_ntax_bonus = 0.0
		total_ntax_bonus = 0.0

		prev_bir = frappe.db.sql(""" SELECT DISTINCT `ntax_bonus` FROM `tabBIR2316` WHERE document_type = "Previous" AND `employee` = %s AND docstatus = 1 LIMIT 1 """, (self.employee), as_dict=1)

		if prev_bir:
			for e in prev_bir:
				prev_ntax_bonus += flt(e.ntax_bonus, 2)

		total_ntax_bonus += prev_ntax_bonus

		ceiling = frappe.db.sql(""" SELECT `value` FROM `tabSingles` WHERE `doctype` = "Payroll Settings" AND `field` = "ceiling_month_pay" LIMIT 1 """, as_dict=True)

		if ceiling:
			for d in ceiling:
				ceiling_limit += flt(d.value, 2) 

			total_ntax_bonus += entry['ntax_bonus']
			total_bonus = total_ntax_bonus + entry['tax_bonus']

			if total_bonus > ceiling_limit:
				entry['tax_bonus'] = total_ntax_bonus - ceiling_limit
				entry['ntax_bonus'] = entry['ntax_bonus'] - entry['tax_bonus']

				entry['ntax_total'] = entry['ntax_total'] - entry['tax_bonus']
				entry['tax_total'] =  entry['tax_total'] + entry['tax_bonus']
			if total_bonus <= ceiling_limit:
				entry['ntax_bonus'] = total_ntax_bonus
				
		return entry