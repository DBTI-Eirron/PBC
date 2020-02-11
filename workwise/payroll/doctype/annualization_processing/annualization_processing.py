# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from calendar import monthrange
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from frappe import _
from frappe.model.document import Document
from workwise.payroll.payroll_utils import get_transaction_map

class AnnualizationProcessing(Document):
	def process_annualization(self):
		ss_list = []
		self.validate_filters()
		from_year, to_year = frappe.db.get_value("Payroll Year", self.payroll_year, ["from_date", "to_date"])

		employees = self.get_employee(from_year, to_year)
		registers = self.get_registers(from_year, to_year)
		previous_bir = self.get_previous_bir(from_year, to_year)
		lastpay = self.get_lastpay(from_year, to_year)

		self.create_entries(employees, registers, previous_bir, lastpay, from_year, to_year)	

		return self.create_log(ss_list)

	def get_employee(self, from_year, to_year):
		employees = frappe.db.sql("""select `name`, tin, full_name, company, tin, date_hired, date_retired, date_resigned, date_terminated, sensitivity from tabEmployee WHERE company = %(company)s 
			AND payroll_schedule = %(schedule)s AND date_hired < %(to_year)s {conditions} 
			ORDER BY full_name ASC """.format( conditions=self.get_employee_conditions() ),
				({ 
					"company": self.company,
					"schedule": self.payroll_schedule,
					"employee": self.employee,
					"from_year": from_year,
					"to_year": to_year,
				}), as_dict=True)

		return employees

	def get_registers(self, from_year, to_year):
		registers = frappe.db.sql("""SELECT PR.name, PR.employee, PR.employee_name, PR.company, PR.posting_date, PR.schedule, PR.gross_payroll,
				PRE.pay_code, PRE.entry_type, PRE.is_taxable, PRE.amount, PR.bonus, PR.monthly_rate, PR.daily_rate FROM `tabPayroll Register Entries` PRE
			INNER JOIN `tabPayroll Register` PR ON PR.`name` = PRE.`parent`
			INNER JOIN `tabPayroll Period` PP ON PR.period = PP.`name`
			WHERE PR.company=%(company)s AND PR.schedule=%(schedule)s {conditions} 
			AND PP.payroll_year = %(payroll_year)s  """.format( conditions=self.get_conditions() ),
				({ 
					"company": self.company,
					"schedule": self.payroll_schedule,
					"employee": self.employee,
					"payroll_year": self.payroll_year,
					"from_year": from_year,
					"to_year": to_year,
				}), as_dict=True)

		return registers

	def get_previous_bir(self, from_year, to_year):
		previous_bir = frappe.db.sql("""SELECT * FROM `tabBIR2316` 
			WHERE payroll_year = %(payroll_year)s AND document_type = "Previous" {conditions} AND docstatus = 1 """.format( conditions=self.get_reg_conditions() ),
				({ 
					"company": self.company,
					"schedule": self.payroll_schedule,
					"employee": self.employee,
					"payroll_year": self.payroll_year,
				}), as_dict=1)

		return previous_bir

	def get_lastpay(self, from_year, to_year):
		lastpay = frappe.db.sql("""SELECT employee, LPR.transaction_type, LPR.amount, LPR.type FROM  `tabLast Pay Entry` LPE 
			INNER JOIN `tabLast Pay Register` LPR ON LPR.parent = LPE.`name`
			WHERE payroll_year = %(payroll_year)s {conditions} """.format( conditions=self.get_reg_conditions() ),
				({ 
					"company": self.company,
					"schedule": self.payroll_schedule,
					"employee": self.employee,
					"payroll_year": self.payroll_year,
				}), as_dict=1)

		return lastpay

	def get_conditions(self):
		conditions = []
		if self.employee:
			conditions.append("PR.employee=%(employee)s")

		return "and {}".format(" and ".join(conditions)) if conditions else ""

	def get_reg_conditions(self):
		conditions = []
		if self.employee:
			conditions.append("employee=%(employee)s")

		return "and {}".format(" and ".join(conditions)) if conditions else ""		

	def get_employee_conditions(self):
		conditions = []
		if self.employee:
			conditions.append("`name`=%(employee)s")

		if frappe.session.user != "Administrator":
			conditions.append(_("sensitivity IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

		return "and {}".format(" and ".join(conditions)) if conditions else ""

	def get_employee_wise_register(self, registers, previous_bir, lastpay, emp_map):
		tr_map = get_transaction_map()
		last_day_nov = monthrange(cint(self.payroll_year), 11)[1]
		last_day_nov = getdate(cstr(""+cstr(self.payroll_year)+"-11-"+cstr(last_day_nov)+""))
		first_day_jan = getdate(cstr(""+cstr(self.payroll_year)+"-1-1"))

		for reg in registers:
			if reg.employee in emp_map:
				if reg.pay_code in tr_map:
					btype = tr_map[reg.pay_code]['bir_type']
					_type = tr_map[reg.pay_code]['type'] 
					is_tax = tr_map[reg.pay_code]['is_taxable']
					if _type != "None":
						#NON-TAXABlE BASIC 
						if (btype == "Basic") and not is_tax:
							emp_map[reg.employee].nt_basic += reg.amount if _type == "Income" else -(reg.amount)
						
						if (btype == "Holiday") and not is_tax:
							emp_map[reg.employee].nt_holiday += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Overtime") and not is_tax:
							emp_map[reg.employee].nt_overtime += reg.amount if _type == "Income" else -(reg.amount)						

						if (btype == "Night Differential") and not is_tax:
							emp_map[reg.employee].nt_nightdiff += reg.amount if _type == "Income" else -(reg.amount)	

						if (btype == "Hazard") and not is_tax:
							emp_map[reg.employee].nt_hazard += reg.amount if _type == "Income" else -(reg.amount)	

						if (btype == "Deminimis") and not is_tax:
							emp_map[reg.employee].nt_demi += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Contribution"): #Contribution is Reversed and Regardless if Taxable or not
							emp_map[reg.employee].nt_contrib += -(reg.amount) if _type == "Income" else reg.amount 

						if (btype == "Other") and not is_tax:
							emp_map[reg.employee].nt_other += reg.amount if _type == "Income" else -(reg.amount)

						#TAXABLE BASIC SALARY
						if (btype == "Basic" or btype == "Contribution") and is_tax: #Contribution Reduce Taxable Basic
							emp_map[reg.employee].t_basic += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Representation") and is_tax:
							emp_map[reg.employee].t_represent += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Transportation") and is_tax:
							emp_map[reg.employee].t_transpo += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "COLA") and is_tax:
							emp_map[reg.employee].t_cola += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Housing") and is_tax:
							emp_map[reg.employee].t_housing += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Commission") and is_tax:
							emp_map[reg.employee].t_comm += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Profit Sharing") and is_tax:
							emp_map[reg.employee].t_sharing += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Fees") and is_tax:
							emp_map[reg.employee].t_fees += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Hazard") and is_tax:
							emp_map[reg.employee].t_hazard += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Overtime") and is_tax:
							emp_map[reg.employee].t_overtime += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Other Regular A") and is_tax:
							emp_map[reg.employee].t_other_a += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Other Regular B") and is_tax:
							emp_map[reg.employee].t_other_b += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Other Supplementary A") and is_tax:
							emp_map[reg.employee].t_other_sa += reg.amount if _type == "Income" else -(reg.amount)

						if (btype == "Other Supplementary B") and is_tax:
							emp_map[reg.employee].t_other_sb += reg.amount if _type == "Income" else -(reg.amount)

						#BENEFITS
						if btype == "13th Month":
							emp_map[reg.employee].total_benefits += reg.amount if _type == "Income" else -(reg.amount)

						#TAX WITHHELD
						if btype == "TAX":
							emp_map[reg.employee].tax_withheld += -(reg.amount) if _type == "Income" else reg.amount
							if first_day_jan <= getdate(reg.posting_date) <= last_day_nov:
								emp_map[reg.employee].withheld_nov += -(reg.amount) if _type == "Income" else reg.amount

		for d in previous_bir:
			if d.employee in emp_map:
				emp_map[d.employee].with_previous = 1
				#PREVIOUS NON-TAXABLE
				emp_map[d.employee].pnt_basic = d.ntax_bs
				emp_map[d.employee].pnt_holiday = d.ntax_ho
				emp_map[d.employee].pnt_overtime = d.ntax_ot
				emp_map[d.employee].pnt_nightdiff = d.ntax_nd
				emp_map[d.employee].pnt_hazard = d.ntax_hazard
				emp_map[d.employee].pnt_benefits = d.ntax_bonus
				emp_map[d.employee].pnt_demi = d.ntax_demi
				emp_map[d.employee].pnt_contrib = d.ntax_contrib
				emp_map[d.employee].pnt_other = d.ntax_other
				emp_map[d.employee].pnt_total = d.ntax_total

				#PREVIOUS TAXABLE
				emp_map[d.employee].pt_basic = d.tax_bs
				emp_map[d.employee].pt_represent = d.tax_rep
				emp_map[d.employee].pt_transpo = d.tax_transpo
				emp_map[d.employee].pt_cola = d.tax_cola
				emp_map[d.employee].pt_housing = d.tax_housing
				emp_map[d.employee].pt_comm = d.tax_commission
				emp_map[d.employee].pt_sharing = d.tax_sharing
				emp_map[d.employee].pt_fees = d.tax_fees
				emp_map[d.employee].pt_benefits = d.tax_bonus
				emp_map[d.employee].pt_hazard = d.tax_hazard
				emp_map[d.employee].pt_overtime = d.tax_ot
				emp_map[d.employee].pt_other_a = d.other_reg_a
				emp_map[d.employee].pt_other_b = d.other_reg_b
				emp_map[d.employee].pt_other_sa = d.other_supp_a
				emp_map[d.employee].pt_other_sb = d.other_supp_b

				#withheld
				emp_map[d.employee].prev_adj_withheld = d.sum_tatwa

				emp_map[d.employee].prev_tax_due = d.sum_td
				emp_map[d.employee].prev_tax_withheld = d.sum_tatwa
				emp_map[d.employee].prev_withheld_nov = d.sum_tatwa

		#LAST PAY
		for lp in lastpay:
			if lp.employee in emp_map:
				if lp.transaction_type in tr_map:
					btype = tr_map[lp.transaction_type]['bir_type']
					_type = lp.type
					is_tax = tr_map[lp.transaction_type]['is_taxable']
					if _type != "None":
						#NON-TAXABlE BASIC 
						if (btype == "Basic") and not is_tax:
							emp_map[lp.employee].nt_basic += lp.amount if _type == "Add" else -(lp.amount)
						
						if (btype == "Holiday") and not is_tax:
							emp_map[lp.employee].nt_holiday += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Overtime") and not is_tax:
							emp_map[lp.employee].nt_overtime += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Night Differential") and not is_tax:
							emp_map[lp.employee].nt_nightdiff += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Hazard") and not is_tax:
							emp_map[lp.employee].nt_hazard += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Deminimis") and not is_tax:
							emp_map[lp.employee].nt_demi += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Contribution"): #Contribution is Reversed and Regardless if Taxable or not
							emp_map[lp.employee].nt_contrib += -(lp.amount) if _type == "Add" else lp.amount 

						if (btype == "Other") and not is_tax:
							emp_map[lp.employee].nt_other += lp.amount if _type == "Add" else -(lp.amount)

						#TAXABLE BASIC SALARY
						if (btype == "Basic" or btype == "Contribution") and is_tax: #Contribution Reduce Taxable Basic
							emp_map[lp.employee].t_basic += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Representation") and is_tax:
							emp_map[lp.employee].t_represent += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Transportation") and is_tax:
							emp_map[lp.employee].t_transpo += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "COLA") and is_tax:
							emp_map[lp.employee].t_cola += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Housing") and is_tax:
							emp_map[lp.employee].t_housing += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Commission") and is_tax:
							emp_map[lp.employee].t_comm += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Profit Sharing") and is_tax:
							emp_map[lp.employee].t_sharing += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Fees") and is_tax:
							emp_map[lp.employee].t_fees += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Hazard") and is_tax:
							emp_map[lp.employee].t_hazard += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Overtime") and is_tax:
							emp_map[lp.employee].t_overtime += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Other Regular A") and is_tax:
							emp_map[lp.employee].t_other_a += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Other Regular B") and is_tax:
							emp_map[lp.employee].t_other_b += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Other Supplementary A") and is_tax:
							emp_map[lp.employee].t_other_sa += lp.amount if _type == "Add" else -(lp.amount)

						if (btype == "Other Supplementary B") and is_tax:
							emp_map[lp.employee].t_other_sb += lp.amount if _type == "Add" else -(lp.amount)

						#BENEFITS
						if btype == "13th Month":
							emp_map[lp.employee].total_benefits += lp.amount if _type == "Add" else -(lp.amount)

						#TAX WITHHELD
						if btype == "TAX":
							emp_map[lp.employee].tax_withheld += -(lp.amount) if _type == "Add" else lp.amount 

	def create_entries(self, employees, registers, previous_bir, lastpay, from_year, to_year):
		emp_map = self.get_employee_map(employees)
		self.get_employee_wise_register(registers, previous_bir, lastpay, emp_map)

		for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
			frappe.db.sql("""DELETE FROM `tabAnnualization Register` WHERE employee = %s AND payroll_year = %s """,(emp, self.payroll_year), as_dict=1)
			ntax_benefits, tax_benefits, tax_due, adj_tax = 0, 0, 0, 0
			ntax_total, amt_withheld, over_withheld = 0, 0, 0
			exclude = 0

			emp_dict.from_date = getdate(from_year)
			emp_dict.to_date = getdate(to_year)
			if getdate(emp_dict.date_hired) > getdate(from_year):
				emp_dict.from_date = getdate(emp_dict.date_hired)

			if emp_dict.date_terminated or emp_dict.date_resigned or emp_dict.date_retired:
				if getdate(emp_dict.date_terminated) <= getdate(to_year):
					emp_dict.is_terminated = 1
					emp_dict.to_date = getdate(emp_dict.date_terminated)
				if getdate(emp_dict.date_resigned) <= getdate(to_year):
					emp_dict.is_terminated = 1
					emp_dict.to_date = getdate(emp_dict.date_resigned)
				if getdate(emp_dict.date_retired) <= getdate(to_year):
					emp_dict.is_terminated = 1
					emp_dict.to_date = getdate(emp_dict.date_retired)
				if getdate(emp_dict.date_contract_ended) <= getdate(to_year):
					emp_dict.is_terminated = 1
					emp_dict.to_date = getdate(emp_dict.date_retired)					
			
			if emp_dict.date_terminated or emp_dict.date_resigned or emp_dict.date_retired:
				if getdate(emp_dict.date_terminated) <= getdate(from_year):
					exclude = 1
				if getdate(emp_dict.date_resigned) <= getdate(from_year):
					exclude = 1
				if getdate(emp_dict.date_retired) <= getdate(from_year):
					exclude = 1
				if getdate(emp_dict.date_contract_ended) <= getdate(from_year):
					exclude = 1

			#Always reduce Basic to contrib
			emp_dict['t_basic'] -= abs(emp_dict['nt_contrib'])

			#calculate if other benefits is beyond the ceiling
			if emp_dict.total_benefits > 90000:
				emp_dict.nt_benefits  = 90000
				emp_dict.t_benefits  = abs(emp_dict.total_benefits - 90000)
			else:
				emp_dict.nt_benefits = emp_dict.total_benefits

			#CURRENT TOTALS
			emp_dict.non_taxable_total = (emp_dict.nt_basic + emp_dict.nt_holiday + emp_dict.nt_overtime + emp_dict.nt_nightdiff + emp_dict.nt_hazard + 
				emp_dict.nt_benefits + emp_dict.nt_demi + emp_dict.nt_contrib + emp_dict.nt_other)

			emp_dict.taxable_total = (emp_dict.t_basic + emp_dict.t_represent + emp_dict.t_transpo + emp_dict.t_cola + emp_dict.t_housing + emp_dict.t_comm + emp_dict.t_sharing + 
				emp_dict.t_fees + emp_dict.t_benefits + emp_dict.t_hazard + emp_dict.t_overtime + emp_dict.t_other_a + emp_dict.t_other_b + emp_dict.t_other_sa + emp_dict.t_other_sb)

			emp_dict.gross_compensation = emp_dict.non_taxable_total + emp_dict.taxable_total
			emp_dict['item_19'] = emp_dict.gross_compensation



			#PREVIOUS TOTALS
			emp_dict.prev_non_taxable_total = (emp_dict.pnt_basic + emp_dict.pnt_holiday + emp_dict.pnt_overtime + emp_dict.pnt_nightdiff + emp_dict.pnt_hazard + 
				emp_dict.pnt_benefits + emp_dict.pnt_demi + emp_dict.pnt_contrib + emp_dict.pnt_other)

			emp_dict.prev_taxable_total = (emp_dict.pt_basic + emp_dict.pt_represent + emp_dict.pt_transpo + emp_dict.pt_cola + emp_dict.pt_housing + emp_dict.pt_comm + emp_dict.pt_sharing + 
				emp_dict.pt_fees + emp_dict.pt_benefits + emp_dict.pt_hazard + emp_dict.pt_overtime + emp_dict.pt_other_a + emp_dict.pt_other_b + emp_dict.pt_other_sa + emp_dict.pt_other_sb)

			emp_dict.prev_gross_compensation = emp_dict.prev_non_taxable_total + emp_dict.prev_taxable_total

			taxable = emp_dict.taxable_total + emp_dict.prev_taxable_total
			table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table`
				WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",(( taxable ), ( taxable ), 'Yearly'), as_dict=True )

			for t in table:
				tax_due = (flt( ( taxable ) , 8) - flt(t.compensatory, 8)) * flt(flt(t.percentage, 8) / 100 , 8)
				if t.prescribed > 0:
					tax_due += flt(t.prescribed, 8)	

			emp_dict.tax_due = tax_due

			#check if tax is to be refunded or to be paid
			withheld = emp_dict.tax_due - (emp_dict.tax_withheld + emp_dict.prev_tax_withheld)

			#Set Amount Withheld & Paid for in December
			emp_dict.adj_amount_withheld = (emp_dict.tax_withheld + emp_dict.prev_tax_withheld) - (emp_dict.withheld_nov + emp_dict.prev_withheld_nov)

			if withheld > 1:
				emp_dict.adj_withheld = abs(withheld)
			elif withheld < 0:
				emp_dict.adj_over_withheld = abs(withheld)
			else:
				emp_dict.adj_withheld = 0

			if taxable < 250000:
				emp_dict.minimum_wage = 1
			else:
				emp_dict.minimum_wage = 0

			if emp_dict.minimum_wage == 1:
				#transfer field values
				emp_dict.nt_basic  = emp_dict.t_basic 
				emp_dict.nt_hazard = emp_dict.t_hazard 
				emp_dict.nt_overtime = emp_dict.t_overtime
				emp_dict['item_20'] = emp_dict.non_taxable_total + emp_dict.t_basic + emp_dict.t_hazard + emp_dict.t_overtime
				#emp_dict.non_taxable_total += emp_dict.taxable_total
				#zero out transfered fields
				emp_dict.t_basic = 0
				emp_dict.t_hazard = 0
				emp_dict.t_overtime = 0
				#emp_dict.taxable_total = 0
			else:
				emp_dict['item_20'] = emp_dict.non_taxable_total
			
			emp_dict['item_21'] = emp_dict.item_19 - emp_dict.item_20
			emp_dict['item_22'] = emp_dict.prev_taxable_total
			emp_dict['item_23'] = emp_dict.item_21 + emp_dict.item_22

			if exclude != 1:
				register = frappe.new_doc("Annualization Register")
				register.update(emp_dict)
				register.insert()

	def get_employee_map(self, employees):
		emp_map = frappe._dict()
		for emp in employees:
			emp_map.setdefault(emp.name, frappe._dict({
					"employee": emp.name,
					"employee_name": emp.full_name,
					"company": emp.company,
					"sensitivity_level": emp.sensitivity,
					"payroll_year": self.payroll_year,
					"tax_id": emp.tin,
					"date_hired": emp.date_hired,
					"from_date": None,
					"to_date": None,
					#TERMINATION DATES
					"date_terminated": emp.date_terminated,
					"date_resigned": emp.date_resigned,
					"date_retired": emp.date_retired,
					#STATUS
					"with_previous": 0,
					"is_terminated": 0,
					"minimum_wage": 0,
					#PREVIOUS NON-TAXABLE
					"pnt_basic": 0,
					"pnt_holiday": 0,
					"pnt_overtime": 0,
					"pnt_nightdiff": 0,
					"pnt_hazard": 0,
					"pnt_benefits": 0,
					"pnt_demi": 0,
					"pnt_contrib": 0,
					"pnt_other": 0,
					"pnt_total": 0,
					#PREVIOUS TAXABLE
					"pt_basic": 0.0,
					"pt_represent": 0,
					"pt_transpo": 0,
					"pt_cola": 0,
					"pt_housing": 0,
					"pt_comm": 0,
					"pt_sharing": 0,
					"pt_fees": 0,
					"pt_benefits": 0,
					"pt_hazard": 0,
					"pt_overtime": 0,
					"pt_other_a": 0,
					"pt_other_b": 0,
					"pt_other_sa": 0,
					"pt_other_sb": 0,
					#NON-TAXABLE
					"nt_basic": 0,
					"nt_holiday": 0,
					"nt_overtime": 0,
					"nt_nightdiff": 0,
					"nt_hazard": 0,
					"nt_benefits": 0,
					"nt_demi": 0,
					"nt_contrib": 0,
					"nt_other": 0,
					#TAXABLE
					"t_basic": 0,
					"t_represent": 0,
					"t_transpo": 0,
					"t_cola": 0,
					"t_housing": 0,
					"t_comm": 0,
					"t_sharing": 0,
					"t_fees": 0,
					"t_benefits": 0,
					"t_hazard": 0,
					"t_overtime": 0,
					"t_other_a": 0,
					"t_other_b": 0,
					"t_other_sa": 0,
					"t_other_sb": 0,
					#TOTALS
					"gross_compensation": 0,
					"total_benefits": 0,
					"non_taxable_total": 0,
					"taxable_total": 0,
					"tax_due": 0,
					"tax_withheld": 0,				
					"adj_amount_withheld": 0,
					"adj_over_withheld": 0,
					"adj_withheld": 0,
					"withheld_nov": 0,
					#PREVIOUS TOTALS
					"prev_withheld_nov": 0,
					"prev_tax_due": 0,
					"prev_tax_withheld": 0,
					"prev_adj_withheld": 0,
					"prev_gross_compensation": 0,
					"prev_total_benefits": 0,
					"prev_non_taxable_total": 0,
					"prev_taxable_total": 0,
				})
			)

		return emp_map

	def validate_filters(self):
		if not self.company:
			frappe.throw(" Company is Required for Annualization Processing")

		if not self.payroll_year:
			frappe.throw(" Year is Required for Annualization Processing")

		if not self.payroll_schedule:
			frappe.throw(" Payroll Schedule is Required for Annualization Processing")

	def include_pro_rated(registers, emp_map):
		tr_map = get_transaction_map()
		included_payreg = []
		entry_pro_rated = {}
		total_bonus = 0

		bonus_method = frappe.db.get_single_value("Payroll Settings", "bonus_method")
		if not bonus_method:
			frappe.throw(_("Please Set Bonus Method in Payroll Settings"))

		for reg in registers:			
			btype = tr_map[reg.pay_code]['bir_type']
			_type = tr_map[reg.pay_code]['type'] 
			is_tax = tr_map[reg.pay_code]['is_taxable']
			ent_type = tr_map[reg.pay_code]['entry_type']

			if reg.employee not in entry_pro_rated:
				entry_pro_rated[reg.employee] = 0

			if bonus_method == "Standard":
				if reg.pay_code == 'BS':
					entry_pro_rated[reg.employee] += reg.amount

			if bonus_method == "Bonus Basis":
				if reg.name not in included_payreg:
					entry_pro_rated[reg.employee] += reg.bonus

			if bonus_method == "Attendance Base":
				if reg.pay_code == 'BS':
					entry_pro_rated[reg.employee] += reg.amount

				if ent_type == 'Attendance':
					if _type == 'Income':
						entry_pro_rated[reg.employee] += reg.amount
					if _type == 'Deduction':
						entry_pro_rated[reg.employee] -= reg.amount

		for ent in entry_pro_rated:
			if entry_pro_rated[ent] > 0:
				entry_pro_rated[ent] = entry_pro_rated[ent]/12
				emp_map[ent].total_benefits += entry_pro_rated[ent]

	def include_lv_conversion(registers, emp_map):
		included_employee = []

		for reg in registers:
			if reg.employee not in included_employee:
				balances = frappe.db.sql("""SELECT LB.* FROM `tabLeave Balance` LB LEFT JOIN `tabLeave Type` LT ON LB.`leave_type`=LT.`name` WHERE LT.`convertible` = 1 AND LB.`employee` = %(employee)s """,{ "employee": reg.employee }, as_dict=True)
				for b in balances:
					credits = (b.credits - b.used_credits)
					emp_map[reg.employee].nt_other += reg.daily_rate * (credits)
				included_employee.append(reg.employee)

	def create_log(self, ss_list):
		log = "<p>" + _("No Annualization Registers Created") + "</p>"
		if ss_list:
			log = "<p>" + _("Annualization Registers Created") + "</p>"
		return log
