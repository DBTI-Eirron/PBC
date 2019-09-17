# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt
#frappe.throw(_("{0}").format(self.get_sss(emp, rates)))

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document
from workwise.payroll.payroll_utils import get_adjustment_settings, get_rates, get_sss_table, get_sss_amount, get_hdmf_table, get_hdmf_amount
from workwise.payroll.weekly_utils import get_weekly_prev_map, get_weekly_basis
from workwise.payroll.loans_utils import get_loans_map, get_employee_loan, update_loans

class PayrollProcessing(Document):
	def get_employees(self):
		employees = frappe.db.sql("""SELECT `name`, full_name, location, company, total_yr_days, rate_type, rate, payroll_schedule, 
			min_take_home, mth_percentage, cost_center, no_hours, 
			sss_mode, sss_manual, sss_freq, phic_mode, phic_manual, phic_freq, hdmf_mode, hdmf_manual, hdmf_freq, whtax_mode, 
			whtax_manual, whtax_freq, is_attendance_base, ignore_late, ignore_nd, ignore_ut, on_hold, sensitivity
				FROM tabEmployee
			WHERE company = %(company)s
			AND payroll_schedule = %(pay_sched)s 
			AND is_active = 1
			{conditions}
			ORDER BY last_name, first_name""".format( conditions=self.get_conditions() ),
			({ 
				"company": self.company,
				"pay_sched": self.schedule,
				"employee": self.employee,
				"department": self.department,
				"location": self.location,
				"period_group": self.period_group,
			}), as_dict=True)

		return employees

	def get_conditions(self):
		conditions = []
		strict_period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')
		if self.employee:
			conditions.append("`name`=%(employee)s")

		if self.department:
			conditions.append("department=%(department)s")

		if self.location:
			conditions.append("location=%(location)s")

		if strict_period_group:
			conditions.append("period_group=%(period_group)s")
		
		if frappe.session.user != "Administrator":
			conditions.append(_("sensitivity IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

		return "and {}".format(" and ".join(conditions)) if conditions else ""

	def validate_period(self, weekly_set):
		period_stats = frappe.db.get_value("Payroll Period", self.period, "status")
		strict_period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')

		if period_stats == "Closed":
			frappe.throw(_("Selected Period is Already Closed"))

		if self.schedule == "Weekly" and not weekly_set:
			frappe.throw(_("Weekly Set id Required for Weekly Period"))			

		if not self.schedule and not self.payroll_date:
			frappe.throw(_("Payroll Schedule and Payroll Date is Required"))

		if strict_period_group and not self.period_group:
			frappe.throw(_("Period Group is required for Payroll Period {0}").format(self.period))

	def process_payroll(self):
		weekly_set = frappe.db.get_value("Payroll Period", self.period, "weekly_set")
		self.validate_period(weekly_set)
		
		no_weeks = ""
		if weekly_set:
			no_weeks = frappe.db.get_value("Weekly Set", weekly_set, "no_weeks")

		ss_list = []
		employees = self.get_employees()
		sss_table = get_sss_table()
		hdmf_table = get_hdmf_table()	
		tr_map = self.get_transaction_map()
		ot_map = self.get_overtime_map()
		adj_settings = get_adjustment_settings()
		previous_period = self.get_previous_period()
		uho_ab_days = frappe.db.get_single_value('Payroll Settings', 'uho_ab_days')
		uho_ab_spnw = frappe.db.get_single_value('Payroll Settings', 'uho_ab_spnw')
		lwop_uho = frappe.db.get_single_value('Payroll Settings', 'hd_lwop_as_uho')
		ex_uho_spnw = frappe.db.get_single_value('Payroll Settings', 'ex_uho_spnw')
		mo_amt_smdl = frappe.db.get_single_value('Payroll Settings', 'mo_amt_smdl')
		hd_no_uho = frappe.db.get_single_value('Payroll Settings', 'hd_no_uho')
		ignore_uho = frappe.db.get_single_value('Payroll Settings', 'ignore_uho')
		whtax_persemi = frappe.db.get_single_value('Payroll Settings', 'whtax_persemi')
		ignore_nd = frappe.db.get_single_value('Timekeeping Settings', 'ignore_nd')
		weekly_prev_map = frappe._dict()
		loans_map = get_loans_map(employees, self.payroll_date, self.period_from, self.period_to)
		if self.schedule == "Weekly":
			weekly_prev_map = get_weekly_prev_map(employees, weekly_set)
		
		if employees:
			no_emp = len(employees)
			proc_emp = 0
			error_emp = 0
			for emp in employees:
				frappe.db.sql("""DELETE FROM `tabPayroll Register` WHERE employee = %s AND period = %s """,(emp.name, self.period ), as_dict=1)
				register = []
				header = {
					'employee': emp.name,
					'employee_name': emp.full_name,
					'company': emp.company,
					'on_hold': emp.on_hold,
					'period_group': self.period_group,
					'posting_date': self.payroll_date,
					'process_date': nowdate(),
					'period': self.period,
					'weekly_set': weekly_set,
					'sensitivity': emp.sensitivity,
					'no_weeks': no_weeks,
					'schedule': self.schedule,
					'frequency': self.frequency,
					'prev_monthly_rate': 0.0,
					'govt_basic': 0.0,
					'hourly_basic': 0.0,
					'sss_inc': 0.0,
					'sss_ded': 0.0,
					'sss_amt': 0.0,
					'phic_inc': 0.0,
					'phic_ded': 0.0,
					'phic_amt': 0.0,
					'hdmf_inc': 0.0,
					'hdmf_ded': 0.0,
					'hdmf_amt': 0.0,
					'whtax_amt': 0.0,
					'bonus_income': 0.0,
					'bonus_deduction': 0.0,
					'taxable_income': 0.0,
					'taxable_deduction': 0.0,
					'total_income': 0.0,
					'total_deduction': 0.0,
					#Attendance
					'work_days': 0.0,
					'absent_days': 0.0,
					'present_days': 0.0,
					'leave_days': 0.0,
					'nwho_days': 0.0,
					'paid_holidays': 0.0,
					'net_payroll': 0.0,
					'gross_payroll': 0.0,
					'bonus': 0.0,
					'cto_days': 0.0,
					#previous cutoff Data
					'prev_govt_basic': 0.0,
					'prev_sss_inc': 0.0,
					'prev_sss_ded': 0.0,
					'prev_sss_amt': 0.0,
					'prev_phic_inc': 0.0,
					'prev_phic_ded': 0.0,
					'prev_phic_amt': 0.0,
					'prev_hdmf_inc': 0.0,
					'prev_hdmf_ded': 0.0,
					'prev_hdmf_amt': 0.0,
					'prev_whtax_amt': 0.0,
					'previous_period': previous_period,
					'previous_taxable_income': 0.0,
					'prev_tax_ded': 0.0,
					'previous_work_days': 0.0,
					'previous_absent_days': 0.0,
					'previous_present_days': 0.0,
					'previous_gross_payroll': 0.0,
					#Payroll Settings
					'uho_ab_days': uho_ab_days,
					'uho_ab_spnw': uho_ab_spnw,
					'lwop_uho': lwop_uho,
					'ex_uho_spnw': ex_uho_spnw,
					'mo_amt_smdl': mo_amt_smdl,
					'hd_no_uho': hd_no_uho,
					'ignore_uho': ignore_uho,
					'ignore_nd': ignore_nd,
					'whtax_persemi' : whtax_persemi,
					'no_attendance': 0,
				}

				#Calculate Rates and Previous Entries
				rates = get_rates(emp)
				self.get_previous(emp, header)

				#Calculate Basic Entries
				self.get_attendance(emp, rates, header, register, ot_map)
				self.get_basic(emp, rates, header, register)
				self.get_recurring(emp, rates, header, register)
				self.get_batch(emp, rates, header, register)
				self.get_adjustment(emp, rates, header, register, adj_settings)
				get_employee_loan(emp, register, loans_map, self.frequency)

				#Calculate Basic Entries to Header
				self.calculate_basic_header(register, header, tr_map)

				#Calculate Special Entries
				self.get_sss(emp, rates, header, register, tr_map, sss_table, weekly_prev_map)
				self.get_phic(emp, rates, header, register, tr_map, weekly_prev_map)
				self.get_hdmf(emp, rates, header, register, tr_map, hdmf_table, weekly_prev_map)
				self.get_whtax(emp, rates, header, register)

				#Calculate Totals
				self.calculate_payroll_totals(header)
				self.calculate_rates_header(header, rates)
				
				#Make Entry
				pr = frappe.new_doc("Payroll Register")
				pr.update(header)
				for d in register:
					if d['amount'] > 0:
						pr.append("payroll_register_entries", {
							"pay_type": tr_map[d.get('pay_code')]['type'],
							"pay_code": d.get('pay_code'),
							"pay_description": tr_map[d.get('pay_code')]['title'],	
							"entry_type": tr_map[d.get('pay_code')]['entry_type'],
							"amount": d.get('amount'),
							"account": tr_map[d.get('pay_code')]['account'],
							"linked_document": d.get('linked_document'),
							"linked_doctype": d.get('linked_doctype'),
							"cost_center": emp.cost_center,
							"is_taxable": tr_map[d.get('pay_code')]['is_taxable'],
							"is_bonus": tr_map[d.get('pay_code')]['is_bonus'],
						})

				#Compute Minimum Wage
				minimum_wage = 0
				if emp.get('mth_percentage'):
					minimum_wage = header.get('basic') * (flt(emp.get('min_take_home'), 8) / 100)
				else:
					minimum_wage = flt(emp.get('min_take_home'), 8)

				if header.get('net_payroll') < minimum_wage and emp.get('min_take_home') > 0:
					payslip_label = " " + emp.full_name +" <span class='label label-danger'> Below Min Take Home </span>"
					ss_list.append(payslip_label)
				else:
					#Check if employee has attendance/work
					if emp.is_attendance_base == 1 and header['no_attendance'] == 1:
						proc_emp += 1
						error_emp += 1
						payslip_label = " " + emp.full_name +"<span class='label label-danger'> No Work </span>"
						ss_list.append(payslip_label)
						
					else:
						if pr.insert():
							#update other entries like loans
							proc_emp += 1
							for d in register:
								if tr_map[d.get('pay_code')]['entry_type'] == 'Loan':
									update_loans(self.payroll_date, d.get('linked_document') , d.get('loan_idx'))
						payslip_label = " " + emp.full_name +""
						if emp.on_hold:
							error_emp += 1
							payslip_label += " <span class='label label-danger'> On-Hold </span>"
						ss_list.append(payslip_label)

			ss_list.append("<b>Processed "+ str(proc_emp)+" / "+str(no_emp)+" Employees ("+str(error_emp)+") with Issues </b>")
		else:
			frappe.throw(_("No Employee Found"))
		
		return self.create_log(ss_list)

	def calculate_basic_header(self, register, header, tr_map):
		for d in register:
			if d.get('amount') > 0:	
				if tr_map[d.get("pay_code")]['type'] == 'Income':
					header['total_income'] += d.get('amount')
					
					if tr_map[d.get("pay_code")]['is_taxable']:
						header['taxable_income'] += d.get('amount')

					if tr_map[d.get("pay_code")]['is_bonus']:
						header['bonus_income'] += d.get('amount')

					if d.get("pay_code") == "BS":
						header['govt_basic'] += d.get('amount')

					if tr_map[d.get("pay_code")]['is_sss'] and d.get("pay_code") != "BS":
						header['sss_inc'] += d.get('amount')

					if tr_map[d.get("pay_code")]['is_phic'] and d.get("pay_code") != "BS":
						header['phic_inc'] += d.get('amount')

					if tr_map[d.get("pay_code")]['is_hdmf'] and d.get("pay_code") != "BS":
						header['hdmf_inc'] += d.get('amount')

				elif tr_map[d.get("pay_code")]['type'] == 'Deduction':
					header['total_deduction'] += d.get('amount')
					
					if tr_map[d.get("pay_code")]['is_taxable']:
						header['taxable_deduction'] += d.get('amount')

					if tr_map[d.get("pay_code")]['is_bonus']:
						header['bonus_deduction'] += d.get('amount')

					if tr_map[d.get("pay_code")]['is_sss'] and d.get("pay_code") != "BS":
						header['sss_ded'] += d.get('amount')

					if tr_map[d.get("pay_code")]['is_phic'] and d.get("pay_code") != "BS":
						header['phic_ded'] += d.get('amount')

					if tr_map[d.get("pay_code")]['is_hdmf'] and d.get("pay_code") != "BS":
						header['hdmf_ded'] += d.get('amount')
	
	def calculate_special_header(self, d, header, tr_map):
		if tr_map[d.get("pay_code")]['type'] == 'Income':
			header['total_income'] += d.get('amount')
			
			if tr_map[d.get("pay_code")]['is_taxable']:
				header['taxable_income'] += d.get('amount')

			if tr_map[d.get("pay_code")]['is_bonus']:
				header['bonus_income'] += d.get('amount')

		elif tr_map[d.get("pay_code")]['type'] == 'Deduction':
			header['total_deduction'] += d.get('amount')
			
			if tr_map[d.get("pay_code")]['is_taxable']:
				header['taxable_deduction'] += d.get('amount')

			if tr_map[d.get("pay_code")]['is_bonus']:
				header['bonus_deduction'] += d.get('amount')

	def calculate_payroll_totals(self, header):
		header['bonus'] = ( header.get('bonus_income') - header.get('bonus_deduction') )
		header['net_payroll'] =  flt(header.get('total_income') - header.get('total_deduction'), 8)
		header['gross_payroll'] = flt(header.get('taxable_income') - header.get('taxable_deduction'), 8)

	def calculate_rates_header(self, header, rates):
		header['monthly_rate'] = rates.get("monthly_rate")
		header['daily_rate'] = rates.get("daily_rate")
		header['hourly_rate'] = rates.get("hourly_rate")

	def get_basic(self, emp, rates, header, register):
		amt = 0
		if emp.get('rate_type') == "Hourly Rate":
			amt = header['hourly_basic']
			rates['monthly_rate'] = amt
		
		elif emp.get('rate_type') == "Daily Rate":
			amt = flt(rates.get('daily_rate'), 8) * (header.get('present_days') + header.get('paid_holidays') )
			if (emp.get('payroll_schedule') == "Semi-Monthly" or emp.get('payroll_schedule') == "Monthly") and header.get('mo_amt_smdl'):
				rates['monthly_rate'] = rates.get('monthly_rate')
			else:
				rates['monthly_rate'] = amt

		elif emp.get('payroll_schedule') == "Weekly":
			amt = rates.get('weekly_rate')

		elif emp.get('payroll_schedule') == "Monthly":
			amt = rates.get('monthly_rate')

		elif emp.get('payroll_schedule') == "Semi-Monthly":
			amt = rates.get('semi_rate')

		header['basic'] = amt
		register.append({"pay_code": "BS", "amount": amt})

	def get_sss(self, emp, rates, header, register, tr_map, sss_table, weekly_prev_map):
		sss_register = []
		if self.frequency == emp.get('sss_freq') or emp.get('sss_freq') == "Both":
			if emp.get('sss_mode') != "None":
				sss_register = []
				sss_list = ["sss","ssse","sssc"]
				sss, ssse, sssc = 0, 0, 0
				target_amt = 0

				if self.schedule == "Weekly":
					if emp.get('sss_mode') == "ME Table":
						if emp.get('sss_freq') == 'Both':
							if cint(header.get("no_weeks")) == cint(5):
								if self.frequency in ["2nd", "5th"]:
									target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12
								else:
									target_amt = 0
									
							elif cint(header.get("no_weeks")) == cint(4):
								if self.frequency in ["2nd", "4th"]:
									target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12
								else:
									target_amt = 0
					else:
						target_amt, monthly_basis = get_weekly_basis(emp, header, emp.get('sss_freq'), self.frequency, weekly_prev_map, flt(header.get('government_basis'), 8) )
 
				else:
					if emp.get('sss_freq') == '1st':
						target_amt = rates.get('monthly_rate') + header.get('sss_inc') - header.get('sss_ded')

					elif emp.get('sss_freq') == '2nd':
						if emp.get('payroll_schedule') == "Semi-Monthly":
							if header.get('prev_monthly_rate') != rates.get('monthly_rate') and header.get('prev_monthly_basis') > 0:
								target_amt = (rates.get('monthly_rate') / 2)+ \
									(header.get('prev_sss_inc') + header.get('sss_inc')) - (header.get('prev_sss_ded') + header.get('sss_ded'))							
							else:
								target_amt = header.get('prev_govt_basic') + header.get('govt_basic') + \
									(header.get('prev_sss_inc') + header.get('sss_inc')) - (header.get('prev_sss_ded') + header.get('sss_ded'))
							
						elif emp.get('payroll_schedule') == "Monthly":
							target_amt = header.get('govt_basic') + header.get('sss_inc') - header.get('sss_ded')

					elif emp.get('sss_freq') == 'Both':
							target_amt = header.get('prev_govt_basic') + header.get('govt_basic') + \
								(header.get('prev_sss_inc') + header.get('sss_inc')) - (header.get('prev_sss_ded') + header.get('sss_ded'))
								
				#Round target_amt to against SSS table	
				sss, ssse, sssc = get_sss_amount(flt(target_amt, 2), sss_table)
				for l in sss_list:
					if emp.get('sss_freq') == "Both" and self.schedule == "Weekly":
						amt = flt(eval(l), 8) / 2
					elif emp.get('sss_freq') == "All" and self.schedule == "Weekly":
						amt = flt(eval(l), 8) / 4
					else:
						amt = flt(eval(l), 8)

					if header.get('prev_sss_amt') and emp.get('sss_freq') == "Both":
						amt = amt - header.get('prev_sss_amt') 
						if amt < 1:
							amt = 0

					sss_register.append({"pay_code": l.upper(), "amount": amt })

			for d in sss_register:
				register.append(d)
				if d.get('pay_code') == "SSS" and d.get('amount') > 0:
					header['sss_amt'] = d.get('amount')

				self.calculate_special_header(d, header, tr_map)

	def get_phic(self, emp, rates, header, register, tr_map, weekly_prev_map):
		phic_register = []
		if self.frequency == emp.get('phic_freq') or emp.get('phic_freq') == 'Both':
			if emp.get('phic_freq') != "None":
				phic_register = []
				phic_list = ["phic","phice"]
				manual = flt(emp.get("phic_manual"), 8)
				mode = emp.get('phic_mode')
				target_amt = 0

				if self.schedule == "Weekly":
					if emp.get('phic_mode') == "ME Table":
						if emp.get('phic_freq') == 'Both':
							if cint(header.get("no_weeks")) == cint(5):
								if self.frequency in ["2nd", "5th"]:
									target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12
								else:
									target_amt = 0
									
							elif cint(header.get("no_weeks")) == cint(4):
								if self.frequency in ["2nd", "4th"]:
									target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12
								else:
									target_amt = 0
					else:
						target_amt, monthly_basis = get_weekly_basis(emp, header, emp.get('phic_freq'), self.frequency, weekly_prev_map, flt(header.get('government_basis'), 8) )

				else:
					if emp.get('phic_mode') == "ME Table":
						target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12
					else:
						if emp.get('phic_freq') == '1st':
							target_amt = header.get('govt_basic') + header.get('phic_inc') - header.get('phic_ded')

						elif emp.get('phic_freq') == '2nd':
							if emp.get('payroll_schedule') == "Semi-Monthly":
								if header.get('prev_monthly_rate') != rates.get('monthly_rate') and header.get('prev_monthly_basis') > 0:
									target_amt = rates.get('monthly_rate') / 2 + \
										(header.get('prev_phic_inc') + header.get('phic_inc')) - (header.get('prev_phic_ded') + header.get('phic_ded'))							
								else:
									target_amt = header.get('prev_govt_basic') + header.get('govt_basic') + \
										(header.get('prev_phic_inc') + header.get('phic_inc')) - (header.get('prev_phic_ded') + header.get('phic_ded'))
								
							elif emp.get('payroll_schedule') == "Monthly":
								target_amt = header.get('govt_basic') + header.get('phic_inc') - header.get('phic_ded')

						elif emp.get('phic_freq') == 'Both':
							target_amt = header.get('prev_govt_basic') + header.get('govt_basic') + \
								(header.get('prev_phic_inc') + header.get('phic_inc')) - (header.get('prev_phic_ded') + header.get('phic_ded'))
				
				if mode != "None" and target_amt:
					phic, phice = 0, 0
					if target_amt < 10000:
						phic = manual if mode == "Manual" and manual > 137.50 else 137.50
						phice = 137.50
					elif target_amt > 39999.99:
						phic = manual if mode == "Manual" and manual > 550.00 else 550.00
						phice = 550.00
					else:
						percent_rate = ( target_amt * (flt(2.75, 8) / 100) / 2)
						phic = manual if mode == "Manual" and manual > percent_rate else percent_rate 
						phice = percent_rate 
					
					for l in phic_list:
						if emp.get('phic_mode') == "ME Table" and self.schedule != "Weekly":
							if emp.get('phic_freq') == "Both":
								amt = flt(eval(l), 8) / 2
							else:
								amt = flt(eval(l), 8)
						else:
							if emp.get('phic_freq') == "Both" and self.schedule == "Weekly":
								amt = flt(eval(l), 8) / 2
							elif emp.get('phic_freq') == "All" and self.schedule == "Weekly":
								amt = flt(eval(l), 8) / 4
							else:
								amt = flt(eval(l), 8)

							if header.get('prev_phic_amt') and emp.get('phic_freq') == "Both":
								amt = amt - header.get('prev_phic_amt') 
								if amt < 1:
									amt = 0

						phic_register.append({"pay_code": l.upper(), "amount": amt })

			for d in phic_register:
				register.append(d)

				if d.get('pay_code') == "PHIC" and d.get('amount') > 0:
					header['phic_amt'] = d.get('amount')

				self.calculate_special_header(d, header, tr_map)

	def get_hdmf(self, emp, rates, header, register, tr_map, hdmf_table, weekly_prev_map):
		hdmf_register = []
		if self.frequency == emp.get('hdmf_freq') or emp.get('hdmf_freq') == 'Both':
			if emp['hdmf_mode'] != "None":
				hdmf_register = []
				hdmf_list = ["hdmf","hdmfe","hdmfm"]
				hdmf, hdmfe, hdmfm = 0, 0, 0
				target_amt = 0

				if self.schedule == "Weekly":
					if emp.get('hdmf_mode') == "ME Table":
						if emp.get('hdmf_freq') == 'Both':
							if cint(header.get("no_weeks")) == cint(5):
								if self.frequency in ["2nd", "5th"]:
									target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12
								else:
									target_amt = 0
									
							elif cint(header.get("no_weeks")) == cint(4):
								if self.frequency in ["2nd", "4th"]:
									target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12
								else:
									target_amt = 0
					else:
						target_amt, monthly_basis = get_weekly_basis(emp, header, emp.get('hdmf_freq'), self.frequency, weekly_prev_map, flt(header.get('government_basis'), 8) )

				else:
					if emp.get('hdmf_freq') == '1st':
						target_amt = header.get('govt_basic') + header.get('hdmf_inc') - header.get('hdmf_ded')

					elif emp.get('hdmf_freq') == '2nd':
						if emp.get('payroll_schedule') == "Semi-Monthly":
							if header.get('prev_monthly_rate') != rates.get('monthly_rate') and header.get('prev_monthly_basis') > 0:
								target_amt = rates.get('monthly_rate') / 2 + \
									(header.get('prev_hdmf_inc') + header.get('hdmf_inc')) - (header.get('prev_hdmf_ded') + header.get('hdmf_ded'))							
							else:
								target_amt = header.get('prev_govt_basic') + header.get('govt_basic') + \
									(header.get('prev_hdmf_inc') + header.get('hdmf_inc')) - (header.get('prev_hdmf_ded') + header.get('hdmf_ded'))
							
						elif emp.get('payroll_schedule') == "Monthly":
							target_amt = header.get('govt_basic') + header.get('phic_inc') - header.get('phic_ded')

					elif emp.get('hdmf_freq') == 'Both':
							target_amt = header.get('prev_govt_basic') + header.get('govt_basic') + \
								(header.get('prev_hdmf_inc') + header.get('hdmf_inc')) - (header.get('prev_hdmf_ded') + header.get('hdmf_ded'))
							
						
				hdmf, hdmfe = get_hdmf_amount(target_amt, hdmf_table)
				if emp.get('hdmf_mode') == "Manual":
					hdmfm = flt(emp.get("hdmf_manual"), 8) - hdmf
					#set to zero if HDMFM is negative
					if hdmfm < 1:
						hdmfm = 0
						
				for l in hdmf_list:
					if emp.get('hdmf_freq') == "Both" and self.schedule == "Weekly":
						amt = flt(eval(l), 8) / 2
					elif emp.get('hdmf_freq') == "All" and self.schedule == "Weekly":
						amt = flt(eval(l), 8) / 4
					else:
						amt = flt(eval(l), 8)

					if header.get('prev_hdmf_amt') and emp.get('hdmf_freq') == "Both":
						amt = amt - header.get('prev_hdmf_amt') 
						if amt < 1:
							amt = 0

					if self.frequency == '1st' and emp.get('payroll_schedule') == "Semi-Monthly" and emp.get('hdmf_freq') == "Both":
						amt = flt(amt, 8) / 2

					hdmf_register.append({"pay_code": l.upper(), "amount": amt })
	
			for d in hdmf_register:
				register.append(d)
				if d.get("pay_code") == "HDMF" and d.get('amount') > 0:
					header['hdmf_amt'] = d.get('amount')

				if d.get("pay_code") == "HDMF" or d.get("pay_code") == "HDMFM":
					self.calculate_special_header(d, header, tr_map)

	def get_whtax(self, emp, rates, header, register):
		taxable = flt(header.get('taxable_income'), 8) - flt(header.get('taxable_deduction'), 8)
		tax_amt = 0
		
		if emp['whtax_mode'] != "None":
			if emp.get('payroll_schedule') == 'Semi-Monthly':
				if header.get('whtax_persemi') == 1 and emp.get('whtax_freq') == "Both":
					table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table`
						WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",(taxable, taxable, 'Semi-Monthly'), as_dict=True )
					
					for t in table:
						tax_amt = (flt(taxable, 8) - flt(t.compensatory, 8)) * flt(flt(t.percentage, 8) / 100 , 8)
						if t.prescribed > 0:
							tax_amt += flt(t.prescribed, 8)
				else:
					if emp.get('whtax_freq') == "Both" and self.frequency == "2nd":
						taxable = flt(header.get('previous_taxable_income'), 8) + flt(header.get('taxable_income'), 8) - \
							( flt(header.get('prev_tax_ded'), 8) + flt(header.get('taxable_deduction'), 8) )
						
						table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table`
								WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",(taxable, taxable, 'Monthly'), as_dict=True )
							
						for t in table:
							tax_amt = (flt(taxable, 8) - flt(t.compensatory, 8)) * flt(flt(t.percentage, 8) / 100 , 8)
							if t.prescribed > 0:
								tax_amt += flt(t.prescribed, 8)

						if header.get('prev_whtax_amt') and emp.get('whtax_freq') == "Both":
							tax_amt = tax_amt - header.get('prev_whtax_amt') 
							if tax_amt < 1:
								tax_amt = 0
					else:
						table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table`
							WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",(taxable, taxable, 'Semi-Monthly'), as_dict=True )
						
						for t in table:
							tax_amt = (flt(taxable, 8) - flt(t.compensatory, 8)) * flt(flt(t.percentage, 8) / 100 , 8)
							if t.prescribed > 0:
								tax_amt += flt(t.prescribed, 8)

			elif emp.get('payroll_schedule') == 'Monthly':
				table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table` 
					WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",(taxable, taxable, 'Monthly'), as_dict=True )

				for t in table:
					tax_amt = (flt(taxable, 8) - flt(t.compensatory ,8)) * flt(flt(t.percentage, 8) / 100 , 8)
					if t.prescribed > 0:
						tax_amt += flt(t.prescribed, 8)

			elif emp.get('payroll_schedule') == 'Weekly':
				table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table` 
					WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",(taxable, taxable, 'Weekly'), as_dict=True )

				for t in table:
					tax_amt = (flt(taxable, 8) - flt(t.compensatory ,8)) * flt(flt(t.percentage, 8) / 100 , 8)
					if t.prescribed > 0:
						tax_amt += flt(t.prescribed, 8)

			register.append({"pay_code": "WHTAX", "amount": tax_amt})
			header['whtax_amt'] = flt(tax_amt, 8)
			header['total_deduction'] += flt(tax_amt, 8)

	def get_recurring(self, emp, rates, header, register):
		att_from, att_to = frappe.db.get_value("Payroll Period", self.period, ["attendance_from", "attendance_to"])
		recurring_register = []
		recurring = frappe.db.sql("""SELECT RE.`name`, RE.method, REE.amount, RE.transaction_type, RE.frequency, RE.date_from, RE.date_to, RE.recurring_type FROM `tabRecurring Entry` RE
			INNER JOIN `tabRecurring Entry Employees` REE ON RE.`name` = REE.parent WHERE REE.employee = %s 
			AND RE.status = 'Enabled' AND RE.company = %s AND RE.docstatus < 2 """,(emp['name'], self.company), as_dict=True )
		
		for rec in recurring :
			if rec.recurring_type == "Range" and not rec.date_from <= att_from <= rec.date_to and not rec.date_from <= att_to <= rec.date_to:
				pass
			else:
				if self.frequency == rec.frequency or rec.frequency == 'Both':
					amt = 0
					if rec.frequency == 'Both':
						if emp.get('payroll_schedule') == "Weekly":
							if cint(header.get("no_weeks")) == cint(5):
								if self.frequency in ["2nd", "5th"]:
									amt = flt(rec.amount, 8) / 2
								else:
									amt = 0
									
							elif cint(header.get("no_weeks")) == cint(4):
								if self.frequency in ["2nd", "4th"]:
									amt = flt(rec.amount, 8) / 2
								else:
									amt = 0
						else:
							amt = flt(rec.amount, 8) / 2
					else:
						amt = rec.amount
					
					if rec.method == "Present Days":
						amt = flt(amt * header.get('present_days'), 8)

					elif rec.method == "Actual Present Days":
						less = 0
						less = (header.get('present_days') + header.get('cto_days')) - (header.get('leave_days') + header.get('nwho_days'))
						if less > 0:
							amt = flt(amt * less, 8)
						else:
							amt = 0

					elif rec.method == 'Work Days':
						amt = flt(amt * header.get('work_days'), 8)
		
					elif rec.method == 'Deduct Absent':
						hourly_rate = self.get_hourly_rate_base(amt, emp)
						
						if header.get('cto_days') > 0:
							absent_days = header.get('absent_days') - header.get('cto_days')
						else:
							absent_days = header.get('absent_days')

						amt = (amt - (( absent_days * 8) * hourly_rate * 2))

					elif rec.method == 'Deduct Absent Actual':
						if header.get('work_days') > 0 and emp.get('no_hours') > 0:
							amt = amt - (( amt / ( header.get('work_days') * emp.get('no_hours') )) * ( header.get('absent_days') * emp.get('no_hours')))
					
					recurring_register.append({
						"linked_document": rec.name,
						"linked_doctype": "Recurring Entry",
						"pay_code": rec.transaction_type,
						"amount": flt(amt, 8),
					})

		for d in recurring_register:
			register.append(d)

	def get_batch(self, emp, rates, header, register):
		batch_register = []
		batch = frappe.db.sql("""SELECT BE.`name`, BEE.amount, BE.transaction_type, BE.period, BE.method
			FROM `tabBatch Entry` BE
			INNER JOIN `tabBatch Entry Employees` BEE ON BE.`name` = BEE.parent
			WHERE BEE.employee = %s AND BE.company = %s AND BE.period = %s
			AND BE.docstatus = 1 """,(emp['name'], self.company, self.period), as_dict=True )

		for d in batch :
			amt = d.amount	
			if d.method == "Present Days":
				amt = flt(amt * header.get('present_days'), 8)

			elif d.method == 'Work Days':
				amt = flt(amt * header.get('work_days'), 8)
			
			elif d.method == 'Deduct Absent':
				hourly_rate = self.get_hourly_rate_base(amt, emp)
				
				if header.get('cto_days') > 0:
					absent_days = header.get('absent_days') - header.get('cto_days')
				else:
					absent_days = header.get('absent_days')

				amt = (amt - (( absent_days * 8) * hourly_rate * 2))

			elif d.method == 'Deduct Absent Actual':
				if header.get('work_days') > 0 and emp.get('no_hours') > 0:
					amt = amt - ((amt / ( header.get('work_days') * emp.get('no_hours') )) * ( header.get('absent_days') * emp.get('no_hours')))

			batch_register.append({
					"linked_document": d.name,
					"linked_doctype": "Batch Entry",
					"pay_code": d.transaction_type,
					"amount": flt(d.amount, 8),
				})

		for d in batch_register:
			register.append(d)

		

	def get_adjustment(self, emp, rates, header, register, adjset):
		adjustment_register = []
		adjustment = frappe.db.sql("""SELECT name, absent, unpaid_holiday, overtime, nightdiff, late, undertime 
			FROM `tabAdjustment Register`WHERE employee = %s AND target_period = %s """,(emp.get('name'), self.period), as_dict=True )
		
		for d in adjustment:
			if d.absent != 0:
				if d.absent < 0:
					adjustment_register.append({
						"linked_document": d.name,
						"linked_doctype": "Adjustment Register",
						"pay_code": adjset.get('inc_ab'),
						"amount": abs(flt(d.absent, 8)),
					})
				else:
					adjustment_register.append({
						"linked_document": d.name,
						"linked_doctype": "Adjustment Register",
						"pay_code": adjset.get('ded_ab'),
						"amount": abs(flt(d.absent, 8)),
					})

			if d.unpaid_holiday != 0:
				if d.unpaid_holiday < 0:
					adjustment_register.append({
						"linked_document": d.name,
						"linked_doctype": "Adjustment Register",
						"pay_code": adjset.get('inc_uho'),
						"amount": abs(flt(d.unpaid_holiday, 8)),
					})
				else:
					adjustment_register.append({
						"linked_document": d.name,
						"linked_doctype": "Adjustment Register",
						"pay_code": adjset.get('ded_uho'),
						"amount": abs(flt(d.unpaid_holiday, 8)),
					})

			#Overtime and Nightdiff is Reversed due to Income Nature
			if d.overtime != 0:
				if d.overtime < 0:
					adjustment_register.append({
						"linked_document": d.name,
						"linked_doctype": "Adjustment Register",
						"pay_code": adjset.get('ded_ot'),
						"amount": abs(flt(d.overtime, 8)),
					})
				else:
					adjustment_register.append({
						"linked_document": d.name,
						"linked_doctype": "Adjustment Register",
						"pay_code": adjset.get('inc_ot'),
						"amount": abs(flt(d.overtime, 8)),
					})

			if frappe.db.get_single_value('Timekeeping Settings', 'ignore_nd') == 0:
				if d.nightdiff != 0:
					if d.nightdiff < 0:
						adjustment_register.append({
							"linked_document": d.name,
							"linked_doctype": "Adjustment Register",
							"pay_code": adjset.get('ded_nd'),
							"amount": abs(flt(d.nightdiff, 8)),
						})
					else:
						adjustment_register.append({
							"linked_document": d.name,
							"linked_doctype": "Adjustment Register",
							"pay_code": adjset.get('inc_nd'),
							"amount": abs(flt(d.nightdiff, 8)),
						})

			if d.late != 0:
				if d.late < 0:
					adjustment_register.append({
						"linked_document": d.name,
						"linked_doctype": "Adjustment Register",
						"pay_code": adjset.get('inc_lt'),
						"amount": abs(flt(d.late, 8)),
					})
				else:
					adjustment_register.append({
						"linked_document": d.name,
						"linked_doctype": "Adjustment Register",
						"pay_code": adjset.get('ded_lt'),
						"amount": abs(flt(d.late, 8)),
					})

			if d.undertime != 0:
				if d.undertime < 0:
					adjustment_register.append({
						"linked_document": d.name,
						"linked_doctype": "Adjustment Register",
						"pay_code": adjset.get('inc_ut'),
						"amount": abs(flt(d.undertime, 8)),
					})
				else:
					adjustment_register.append({
						"linked_document": d.name,
						"linked_doctype": "Adjustment Register",
						"pay_code": adjset.get('ded_ut'),
						"amount": abs(flt(d.undertime, 8)),
					})

		for d in adjustment_register:
			register.append(d)

	def get_hourly_rate_base(self, amt, emp):
		hourly_rate = 0
		if amt > 0 and  emp.get('total_yr_days') > 0 and emp.get('no_hours') > 0:
			month_days = (flt( emp.get('total_yr_days') , 8) / 12)
			if emp.get('rate_type') == "Monthly Rate":
				hourly_rate = ( flt(amt , 8) / month_days ) / emp.get('no_hours')
			elif emp.get('rate_type') == "Hourly Rate":
				hourly_rate = flt(amt , 8)
			elif emp.get('rate_type') == "Daily Rate":
				hourly_rate = flt(amt , 8) / emp.get('no_hours')

		return hourly_rate

	def get_attendance(self, emp, rates, header, register, ot_map):
		attendance_register = []
		if emp.get('is_attendance_base') > 0:
			late, overtime, undertime, absent, nightdiff, cto, cto_days, work_days, absent_days = 0, 0, 0, 0, 0, 0, 0, 0, 0
			unpaid_holiday, prev_lwop, prev_absent, is_uho, leave_days, nwho_days, total_work  =  0, 0 ,0, 0, 0, 0, 0
			pho_days, uho_days, dl_days = 0, 0, 0.0
			hourly_basic, no_previous = 0, 0
			test = []

			attendance = frappe.db.sql("""SELECT * FROM `tabAttendance Register` 
				WHERE employee = %s AND target_date >= %s AND target_date <= %s ORDER BY target_date """,(emp['name'], add_days(self.attendance_from, -1), self.attendance_to), as_dict=1)

			overtime_list = frappe.db.sql("""SELECT employee, target_date, ot_code, hrs, linked_ot FROM `tabOvertime` 
				WHERE employee = %s AND target_date >= %s AND target_date <= %s ORDER BY target_date """,(emp.get('name'), self.attendance_from, self.attendance_to), as_dict=1)
			
			for ot in overtime_list:
				if ot.ot_code in ot_map:
					overtime += flt( ot.hrs, 8) * rates.get('hourly_rate') * (ot_map[ot.get('ot_code')]['rate'] / 100)
				else:
					overtime += flt( ot.hrs, 8) * rates.get('hourly_rate')

			if attendance:
				for at in attendance:
					WK_days, AT_days = 0, 0
					
					
					if getdate(at.target_date) == getdate(add_days(self.attendance_from, -1)):
						no_previous = 1
						if at.is_absent or at.is_lwop:
							is_uho = 1
							if header.get('lwop_uho') == 1:
								if (at.lv_status == 2 or at.lv_status == 3) or at.is_halfday:
									is_uho = 0
									if at.is_absent:
										is_uho = 1
					else:
						if no_previous == 0:
							is_uho = 1

						if not at.is_restday:
							WK_days += 1
							work_days += 1

						if at.late > 0:
							late += flt(at.late, 8) * flt(rates.get('hourly_rate'), 8)
						
						if at.undertime > 0:
							undertime += flt(at.undertime, 8) * flt(rates.get('hourly_rate'), 8)

						if at.nightdiff:
							nightdiff += at.nightdiff * 0.10 * rates.get('hourly_rate')

						if ( at.is_absent == 1 or at.is_lwop == 1 ) and not at.is_holiday:
							if at.is_lwop == 1 and at.lv_status > 1:
								absent += ( at.work_hours / 2 ) * flt(rates.get('hourly_rate'), 8)
								absent_days += 0.5
								AT_days += 0.5
							else:
								absent += ( at.work_hours / 2 ) * flt(rates.get('hourly_rate'), 8) if at.is_halfday == 1 else ( at.work_hours ) * flt(rates.get('hourly_rate'), 8)
								absent_days += 0.5 if at.is_halfday == 1 else 1
								AT_days += 0.5 if at.is_halfday == 1 else 1

						if at.cto:
							max_cto = 0
							max_cto += at.undertime
							max_cto += at.late
							if ( at.is_absent == 1 or at.is_lwop == 1 ) and not at.is_holiday:
								if at.is_lwop == 1 and at.lv_status > 1:
									max_cto += ( at.work_hours / 2 )
								else:
									max_cto += ( at.work_hours / 2 ) if at.is_halfday == 1 else at.work_hours

							if max_cto < at.cto:
								cto += ( max_cto ) * flt(rates.get('hourly_rate'), 8)
							else:
								cto += ( at.cto ) * flt(rates.get('hourly_rate'), 8)

							if at.is_absent == 1:
								if at.is_halfday == 1 and max_cto >= (at.work_hours / 2):
									cto_days += 0.5
								elif max_cto >= at.work_hours:
									cto_days += 1

						if emp.get("rate_type") == "Daily Rate":
							dl_absent = 1 #set default alaways absent
							ho_paid = 0 # set default not paid on holiday

							#check if employee is not absent
							if(at.work or (not at.is_absent)) and (not at.is_lwop):
								dl_absent = 0

							#if did not worked on a holiday tagged as uho uho
							if at.is_holiday and at.work < 1 and not (at.is_restday):
								dl_absent = 1

							#leave triggers
							if at.lv_status == 1 and (not at.is_lwop):
								dl_absent = 0

							#check if holiday
							if at.is_holiday:
								if at.is_restday:
									if (not at.is_sp_holiday) and (not is_uho):
										ho_paid = 1 #paid on regular holiday if not UHO
								else:
									if dl_absent == 1 and at.is_sp_holiday and header.get('uho_ab_spnw'):
										ho_paid = 0 #no paid holiday on special HO
									elif dl_absent == 1 and (not is_uho):
										ho_paid = 1 #paid holiday if absent and not UHO
									elif dl_absent == 0:
										ho_paid = 1 #paid holiday if not absent and not UHO
							else: 
								if dl_absent == 0 and (not at.is_restday):
									if at.is_halfday:
										dl_days += 0.5
									else:
										dl_days += 1

							if ho_paid == 1:
								pho_days += 1

						if at.is_holiday == 1 and is_uho == 1 and (not at.is_ob) and not at.is_restday:
							#if present not UHO
							if emp.get("rate_type") != "Daily Rate":
								if at.work and (not at.is_lwop) and (not at.absent) and (not at.is_restday) and (not at.is_halfday):
									is_uho = 0
								else:
									unpaid_holiday += at.work_hours * flt(rates.get('hourly_rate'), 8)
									if header.get('uho_ab_days') == 1:
										absent_days += 1
										AT_days += 1

						#check if this attendance is lwop or absent for next attendance
						if is_uho == 1:
							#if present
							if at.work and (not at.is_lwop) and (not at.absent) and (not at.is_restday) and (not at.is_halfday):
								is_uho = 0

							#if Halfday next day
							if header.get('hd_no_uho') and at.is_halfday:
								is_uho = 0

							#if Proper Leave next day is not UHO
							if at.lv_status == 1 and not at.is_lwop:
								is_uho = 0

							#if proper OB next day is not UHO
							if at.is_ob:
								is_uho = 0	

							#UHO if Absent and leave withoutpay
							if at.is_absent and at.is_lwop:
								is_uho = 1

							#Not UHO if halfday and halfday leave
							if (at.lv_status == 2 or at.lv_status == 3) and at.is_halfday:
								is_uho = 0
								if header.get('lwop_uho') == 1 and at.is_lwop:
									is_uho = 1
						
							#strictly No UHO if CTO can cover absent work hours
							if at.is_absent and at.work_hours <= at.cto:
								is_uho = 0						
						else:
							is_uho = 0
							if (at.is_absent or at.is_lwop) and not at.is_ob:
								is_uho = 1

								if header.get('lwop_uho') == 1:
									if (at.lv_status == 2 or at.lv_status == 3) and at.is_halfday:
										is_uho = 0
										if at.is_absent:
											is_uho = 1

							#If Halfday is LWOP but not absent
							if header.get('lwop_uho') == 1:
								if (at.lv_status == 2 or at.lv_status == 3) and at.is_lwop and (not at.is_absent):
									is_uho = 0
							
							#strictly No UHO if CTO can cover absent work hours
							if at.is_absent and at.work_hours <= at.cto:
								is_uho = 0

							#if Halfday next day will not be UHO
							if header.get('hd_no_uho') and at.is_halfday:
								is_uho = 0

						if emp.get("rate_type") == "Hourly Rate":
							hour_bs = ((WK_days - AT_days) * at.work_hours) * flt(rates.get('hourly_rate'), 8)
							hourly_basic += hour_bs

						#Check if employee has attendance
						if at.work:
							total_work += at.work

				header['no_attendance'] = 1
				if total_work > 0:
					header['no_attendance'] = 0

				#Get Presentdays and Daily Rate should have no absent
				if emp.get("rate_type") == "Daily Rate":
					absent = 0
					present_days = dl_days
				else:
					present_days =  work_days - absent_days

				if header.get('ignore_uho'):
					unpaid_holiday = 0

				if emp.get('ignore_late'):
					late = 0

				if emp.get('ignore_ut'):
					undertime = 0

				if emp.get('ignore_nd') or header.get('ignore_nd'):
					nightdiff = 0

				attendance_register.append({"pay_code": "AT", "amount": flt(absent, 8) })
				attendance_register.append({"pay_code": "CTO", "amount": flt(cto, 8) })
				attendance_register.append({"pay_code": "UHO", "amount": flt(unpaid_holiday, 8) })
				attendance_register.append({"pay_code": "OT", "amount": flt(overtime, 8) })
				attendance_register.append({"pay_code": "ND", "amount": flt(nightdiff, 8) })
				attendance_register.append({"pay_code": "LT", "amount": flt(late, 8) })
				attendance_register.append({"pay_code": "UT", "amount": flt(undertime, 8) })
				
				for d in attendance_register:
					register.append(d)

				header['cto_days'] = cto_days
				header['work_days'] = work_days
				header['absent_days'] = absent_days
				header['present_days'] = present_days
				header['paid_holidays'] = pho_days
			else:
				header['no_attendance'] = 1

	def get_transaction_map(self):
		tr_map = {}
		tr = frappe.db.sql("""SELECT code, title, type, entry_type, account, is_taxable, is_bonus, is_government, is_standard, is_active, is_sss, is_phic, is_hdmf FROM `tabTransaction Type` """, as_dict=1)
		for t in tr:
			tr_map[t.code] = {"code": t.code, "title": t.title, "type": t.type, "entry_type": t.entry_type,	"account": t.account, 
				"is_taxable": t.is_taxable, "is_standard": t.is_standard, "is_active": t.is_active, "is_bonus": t.is_bonus, "is_government": t.is_government,
				"is_sss": t.is_sss, "is_phic": t.is_phic, "is_hdmf": t.is_hdmf,
			}

		return tr_map

	def get_overtime_map(self):
		ot_map = {}
		ot = frappe.db.sql(""" SELECT `name`, ot_code, ot_rate FROM `tabOvertime Rates` """, as_dict=1)
		for t in ot:
			ot_map[t.ot_code] = {
				"rate": t.ot_rate,
				"name": t.name,
			}
		return ot_map

	def get_previous_period(self):
		previous_period = ""
		if self.schedule != "Weekly" and self.frequency != '1st':
			before = frappe.db.sql_list(""" SELECT `name` FROM `tabPayroll Period` WHERE company = %s 
				AND `schedule` = %s AND payroll_date < %s ORDER BY payroll_date DESC LIMIT 1 """,(self.company, self.schedule, self.payroll_date ))
			
			previous_period = before[0] if before else ""

		return previous_period

	def get_previous(self, emp, header):
		if self.schedule != "Weekly":
			previous = frappe.db.sql(""" SELECT monthly_rate, taxable_income, taxable_deduction, gross_payroll, 
				present_days, work_days, absent_days, govt_basic,
				sss_inc, sss_ded, sss_amt, phic_inc, phic_ded, phic_amt, hdmf_inc, hdmf_ded, hdmf_amt, whtax_amt
				FROM `tabPayroll Register` 
				WHERE period = %s AND employee = %s LIMIT 1 """,(header.get('previous_period'), emp.get('name')), as_dict=True)		
			for d in previous:
				header['prev_monthly_rate'] = flt(d.monthly_rate, 8)
				header['prev_govt_basic'] = flt(d.govt_basic, 8)
				header['prev_sss_inc'] = flt(d.sss_inc, 8)
				header['prev_sss_ded'] = flt(d.sss_ded, 8)
				header['prev_sss_amt'] = flt(d.sss_amt, 8)
				header['prev_phic_inc'] = flt(d.phic_inc, 8)
				header['prev_phic_ded'] = flt(d.phic_ded, 8)
				header['prev_phic_amt'] = flt(d.phic_amt, 8)
				header['prev_hdmf_inc'] = flt(d.hdmf_inc, 8)
				header['prev_hdmf_ded'] = flt(d.hdmf_ded, 8)
				header['prev_hdmf_amt'] = flt(d.hdmf_amt, 8)
				header['prev_whtax_amt'] = flt(d.whtax_amt, 8)
				header['previous_taxable_income'] = flt(d.taxable_income, 8)
				header['prev_tax_ded'] = flt(d.taxable_deduction, 8)
				header['previous_gross_payroll'] = flt(d.gross_payroll, 8)
				header['previous_present_days'] = flt(d.present_days, 8)
				header['previous_work_days'] = flt(d.work_days, 8)
				header['previous_absent_days'] = flt(d.absent_days, 8)

	def create_log(self, ss_list):
		log = "<p>" + _("No Employee for the above selected criteria Payroll or Already Created") + "</p>"
		if ss_list:
			log = "<b>" + _("Payroll Registers Created") + "</b>\
			<br><br>%s" % '<br>'.join(self.format_as_links(ss_list))
		return log

	def format_as_links(self, ss_list):
		return ['{0}'.format(s) for s in ss_list]