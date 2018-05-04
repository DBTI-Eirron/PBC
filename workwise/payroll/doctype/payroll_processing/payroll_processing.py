# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt
#frappe.throw(_("{0}").format(self.get_sss(emp, rates)))

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document

class PayrollProcessing(Document):
	def get_employees(self):
		if self.employee:
			employees = frappe.db.sql("""SELECT `name`, full_name, location, company, total_yr_days, rate_type, rate, payroll_schedule, min_take_home, cost_center, no_hours, 
				sss_mode, sss_manual, sss_freq, phic_mode, phic_manual, phic_freq, hdmf_mode, hdmf_manual, hdmf_freq, whtax_mode, whtax_manual, whtax_freq, is_attendance_base
					FROM tabEmployee
					WHERE company = %(company)s
				AND `name` = %(employee)s
				AND payroll_schedule = %(pay_sched)s 
				AND on_hold = 0
				AND is_active = 1 ORDER BY last_name, first_name""",{ 
					"company": self.company,
					"pay_sched": self.schedule,
					"employee": self.employee
				}, as_dict=True)
		else:
			employees = frappe.db.sql("""SELECT `name`, full_name, location, company, total_yr_days, rate_type, rate, payroll_schedule, min_take_home, cost_center, no_hours, 
				sss_mode, sss_manual, sss_freq, phic_mode, phic_manual, phic_freq, hdmf_mode, hdmf_manual, hdmf_freq, whtax_mode, whtax_manual, whtax_freq, is_attendance_base
					FROM tabEmployee
					WHERE company = %(company)s
				AND payroll_schedule = %(pay_sched)s 
				AND on_hold = 0
				AND is_active = 1 ORDER BY last_name, first_name""",{ 
					"company": self.company,
					"pay_sched": self.schedule
				}, as_dict=True)

		return employees

	def validate_period(self):
		period_stats = frappe.db.get_value("Payroll Period", self.period, "status")
		if period_stats == "Closed":
			frappe.throw(_("Selected Period is Already Closed"))

		if not self.schedule and not self.payroll_date:
			frappe.throw(_("Fill up Mandatory Fields"))

	def process_payroll(self):
		self.validate_period()
		ss_list = []
		employees = self.get_employees()
		tr_map = self.get_transaction_map()
		ot_map = self.get_overtime_map()
		previous_period = self.get_previous_period()

		if employees:
			for emp in employees:
				exist =  frappe.db.sql("""SELECT `name` FROM `tabPayroll Register` WHERE employee = %s AND period = %s """,(emp.name, self.period ), as_dict=1)
				if exist:
					for ex in exist:
						frappe.delete_doc("Payroll Register", ex.name)
			
				register = []
				header = {
					'employee': emp.name,
					'employee_name': emp.full_name,
					'company': emp.company,
					'posting_date': self.payroll_date,
					'process_date': nowdate(),
					'period': self.period,
					'schedule': self.schedule,
					'process_type': self.process_type,
					'frequency': self.frequency,
					'previous_period': previous_period,
					'previous_taxable_income': 0.0,
					'previous_work_days': 0.0,
					'previous_absent_days': 0.0,
					'previous_present_days': 0.0,
					'previous_gross_payroll': 0.0,
					'previous_government_basis': 0.0,
					'bonus_income': 0.0,
					'bonus_deduction': 0.0,
					'taxable_income': 0.0,
					'taxable_deduction': 0.0,
					'total_income': 0.0,
					'total_deduction': 0.0,
					'government_basis': 0.0,
					'work_days': 0.0,
					'absent_days': 0.0,
					'present_days': 0.0,
					'net_payroll': 0.0,
					'gross_payroll': 0.0,
					'bonus': 0.0,
				}

				#Calculate Rates and Previous Entries
				rates = self.get_rates(emp)
				self.get_previous(emp, header)

				#Calculate Basic Entries
				self.get_attendance(emp, rates, header, register, ot_map)
				self.get_basic(emp, rates, header, register)
				self.get_recurring(emp, rates, header, register)
				self.get_batch(emp, rates, register)
				self.get_loans(emp, rates, register)

				#Calculate Basic Entries to Header
				self.calculate_basic_header(register, header, tr_map) 

				#Calculate Special Entries
				self.get_sss(emp, rates, header, register, tr_map)
				self.get_phic(emp, rates, header, register, tr_map)
				self.get_hdmf(emp, rates, header, register, tr_map)
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

				if pr.insert():
					#update other entries like loans
					for d in register:
						if tr_map[d.get('pay_code')]['entry_type'] == 'Loan':
							self.update_loans(d.get('linked_document'))

				payslip_label = " " + emp.full_name +""
				ss_list.append(payslip_label)
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

					if tr_map[d.get("pay_code")]['is_government']:
						header['government_basis'] += d.get('amount')

				elif tr_map[d.get("pay_code")]['type'] == 'Deduction':
					header['total_deduction'] += d.get('amount')
					
					if tr_map[d.get("pay_code")]['is_taxable']:
						header['taxable_deduction'] += d.get('amount')

					if tr_map[d.get("pay_code")]['is_bonus']:
						header['bonus_deduction'] += d.get('amount')

					if tr_map[d.get("pay_code")]['is_government']:
						header['government_basis'] -= d.get('amount')
	
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

	def get_basic(self, emp, rates, header, register):
		amt = 0
		if emp.get('rate_type') == "Hourly Rate":
			amt = flt(rates.get('hourly_rate'), 8) * (header.get('present_days') / emp.get('no_hours'))
			rates['monthly_rate'] = amt
		
		elif emp.get('rate_type') == "Daily Rate":
			amt = flt(rates.get('daily_rate'), 8) * header.get('present_days')
			rates['monthly_rate'] = amt

		elif emp.get('payroll_schedule') == "Monthly":
			amt = rates.get('monthly_rate')

		elif emp.get('payroll_schedule') == "Semi-Monthly":
			amt = rates.get('semi_rate')

		register.append({"pay_code": "BS", "amount": amt})

	def get_sss(self, emp, rates, header, register, tr_map):
		sss_register = []
		if self.frequency == emp.get('sss_freq') or emp.get('sss_freq') == "Both":
			if emp.get('sss_mode') != "None":
				sss_register = []
				sss_list = ["sss","ssse","sssc"]
				sss, ssse, sssc = 0, 0, 0
				target_amt = header.get('government_basis')

				if emp['sss_freq'] == '2nd':
					target_amt += flt(header.get('previous_government_basis'), 8)
				elif emp['sss_freq'] == 'Both':
					target_amt += header.get('government_basis')

				table = frappe.db.sql("""SELECT employee, employer, ec FROM `tabSSS Table`
					WHERE %s >= beginning AND %s <= ending LIMIT 1 """,( target_amt, target_amt ), as_dict=True )

				for t in table:
					sss = flt(emp["sss_manual"], 8) if emp.get('sss_mode') == "Manual" and flt(emp["sss_manual"], 8) > t.employee else t.employee
					ssse, sssc = t.employer, t.ec

				for l in sss_list:
					amt = flt(eval(l), 8) / 2 if emp['sss_freq'] == "Both" else flt(eval(l), 8)
					sss_register.append({"pay_code": l.upper(), "amount": amt })

			for d in sss_register:
				register.append(d)
				self.calculate_special_header(d, header, tr_map)

	def get_phic(self, emp, rates, header, register, tr_map):
		phic_register = []
		if self.frequency == emp['phic_freq'] or emp.get('phic_freq') == 'Both':
			phic_register = []
			phic_list = ["phic","phice"]
			manual = flt(emp.get("phic_manual"), 8)
			mode = emp.get('phic_mode')
			target_amt = flt(header.get('government_basis'), 8)

			if emp['phic_freq'] == '2nd':
				target_amt += flt(header.get('previous_government_basis'), 8)
			elif emp['sss_freq'] == 'Both':
				target_amt += flt(header.get('government_basis'), 8)


			if mode != "None":
				phic, phice = 0, 0
				if target_amt < 10000:
					phic = manual if mode == "Manual" and manual > 137.50 else 137.50
					phice = 137.50
				elif target_amt > 39999.99:
					phic = manual if mode == "Manual" and manual > 550.00 else 550.00
					phice = 550.00
				else:
					percent_rate = ( target_amt * (flt(2.75, 2) / 100) / 2)
					phic = manual if mode == "Manual" and manual > percent_rate else percent_rate 
					phice = percent_rate 
				
				for l in phic_list:
					amt = flt(eval(l), 8) / 2 if emp['phic_freq'] == "Both" else flt(eval(l), 8)
					phic_register.append({"pay_code": l.upper(), "amount": amt })

			for d in phic_register:
				register.append(d)
				self.calculate_special_header(d, header, tr_map)

	def get_hdmf(self, emp, rates, header, register, tr_map):
		hdmf_register = []
		if self.frequency == emp['hdmf_freq'] or emp.get('phic_freq') == 'Both':
			if emp['hdmf_mode'] != "None":
				hdmf_register = []
				hdmf_list = ["hdmf","hdmfe"]
				hdmf, hdmfe = 0, 0

				target_amt = flt(header.get('government_basis'), 8)
				if emp['phic_freq'] == '2nd':
					target_amt += flt(header.get('previous_government_basis'), 8)

				table = frappe.db.sql("""SELECT employee, employer FROM `tabHDMF Table` 
					WHERE %s >= beginning AND %s <= ending LIMIT 1 """,(target_amt, target_amt), as_dict=True )

				for t in table:
					hdmf = flt(emp["hdmf_manual"], 8) if emp['hdmf_mode'] == "Manual" and flt(emp["hdmf_manual"], 8) > t.employee else t.employee
					hdmfe = t.employer

				for l in hdmf_list:
					amt = flt(eval(l), 8) / 2 if emp['hdmf_freq'] == "Both" else flt(eval(l), 8)
					hdmf_register.append({"pay_code": l.upper(), "amount": amt })
		
			for d in hdmf_register:
				register.append(d)
				if d.get("pay_code") == "HDMF":
					self.calculate_special_header(d, header, tr_map)

	def get_whtax(self, emp, rates, header, register):
		taxable = flt(header.get('taxable_income'), 8) - flt(header.get('taxable_deduction'), 8)
		tax_amt = 0
		
		if emp['whtax_mode'] != "None":
			if emp['whtax_freq'] == 'Both':
				taxable += taxable
				table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table`
					WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",(taxable, taxable, 'Monthly'), as_dict=True )

				for t in table:
					tax_amt = (flt(taxable, 8) - flt(t.compensatory, 8)) * flt(flt(t.percentage, 8) / 100 , 8) / 2
					if t.prescribed > 0:
						tax_amt += flt(t.prescribed, 8)
			else:	
				if emp['whtax_freq'] == '2nd':
					if emp['payroll_schedule'] == "Semi-Monthly":
						taxable += flt(header.get('previous_gross_payroll'), 8)

				table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table` 
					WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",(taxable, taxable, 'Monthly'), as_dict=True )

				for t in table:
					tax_amt = (flt(taxable, 8) - flt(t.compensatory ,8)) * flt(flt(t.percentage, 8) / 100 , 8)
					if t.prescribed > 0:
						tax_amt += flt(t.prescribed, 8)

			register.append({"pay_code": "WHTAX", "amount": tax_amt})
			header['total_deduction'] += flt(tax_amt, 8)

	def get_recurring(self, emp, rates, header, register):
		recurring_register = []
		recurring = frappe.db.sql("""SELECT RE.`name`, RE.method, REE.amount, RE.transaction_type, RE.frequency FROM `tabRecurring Entry` RE
			INNER JOIN `tabRecurring Entry Employees` REE ON RE.`name` = REE.parent WHERE REE.employee = %s 
			AND RE.status = 'Enabled' AND RE.company = %s AND RE.docstatus < 2 """,(emp['name'], self.company), as_dict=True )
		for rec in recurring :
			if self.frequency == rec.frequency or rec.frequency == 'Both':
				amt = rec.amount
				if rec.frequency == 'Both':
					amt = flt(rec.amount, 8) / 2
				
				if rec.method == "Present Days":
					amt = flt(amt * header['present_days'], 8)

				recurring_register.append({
						"linked_document": rec.name,
						"linked_doctype": "Recurring Entry",
						"pay_code": rec.transaction_type,
						"amount": flt(amt, 8),
					})
		for d in recurring_register:
			register.append(d)

	def get_batch(self, emp, rates, register):
		batch_register = []
		batch = frappe.db.sql("""SELECT BE.`name`, BEE.amount, BE.transaction_type, BE.period
			FROM `tabBatch Entry` BE
			INNER JOIN `tabBatch Entry Employees` BEE ON BE.`name` = BEE.parent
			WHERE BEE.employee = %s AND BE.company = %s AND BE.period = %s
			AND BE.docstatus = 1 """,(emp['name'], self.company, self.period), as_dict=True )
		for d in batch :
			batch_register.append({
					"linked_document": d.name,
					"linked_doctype": "Batch Entry",
					"pay_code": d.transaction_type,
					"amount": flt(d.amount, 8),
				})

		for d in batch_register:
			register.append(d)

	def get_loans(self, emp, rates, register):
		loans_register = []
		frappe.db.sql("""UPDATE `tabLoan Application Payments` LAP INNER JOIN `tabLoan Application` LA ON LAP.parent = LA.name
			SET LAP.payment_status = 'Unpaid', LAP.payment_date = NULL
			WHERE LA.employee = %s AND LAP.payment_date = %s AND LAP.payment_status = 'Paid' """,(emp['name'], self.payroll_date), as_dict=True )

		loans = frappe.db.sql("""SELECT LA.`name`, LA.release_date, LA.loan_type, LA.loan_amount, MAX(LAP.payment_amount) as payment_amount, LA.payment_frequency
			FROM `tabLoan Application` LA INNER JOIN `tabLoan Application Payments` LAP ON LA.`name` = LAP.parent
			WHERE LA.employee = %s AND LA.payment_start <= %s AND LAP.payment_status = 'Unpaid' AND LA.docstatus = 1
			GROUP BY LA.`name` """,(emp['name'], self.payroll_date), as_dict=True )

		for l in loans:
			if l.payment_frequency == self.frequency or l.payment_frequency == 'Both':
				loans_register.append({
						"linked_document": l.name,
						"linked_doctype": "Loan Application",
						"pay_code": l.loan_type,
						"amount": flt(l.payment_amount, 2),
					})

		for d in loans_register:
			register.append(d)

	def update_loans(self, loan_doc):
		if loan_doc:
			payment = frappe.db.sql("""SELECT `name` FROM `tabLoan Application Payments`
				WHERE parent = %s AND payment_date = %s AND payment_status = 'Paid' """,(loan_doc, self.payroll_date), as_dict=True )
			
			if not payment:
				total_paid, total_unpaid = 0, 0
				frappe.db.sql("""UPDATE `tabLoan Application Payments` SET payment_status = 'Paid', payment_date = %s
					WHERE parent = %s AND payment_status = 'Unpaid' ORDER BY idx LIMIT 1 """,(self.payroll_date, loan_doc), as_dict=True )

				payments = frappe.db.sql("""SELECT payment_status, payment_amount FROM `tabLoan Application Payments` 
					WHERE parent = %s""",(loan_doc), as_dict=True )
				for p in payments:
					if p.payment_status == 'Paid':
						total_paid += p.payment_amount
					else:
						total_unpaid += p.payment_amount

				frappe.db.sql("""UPDATE `tabLoan Application` SET unpaid_amount = %s, paid_amount = %s
					WHERE name = %s LIMIT 1 """,(total_unpaid, total_paid, loan_doc), as_dict=True )

	def get_attendance(self, emp, rates, header, register, ot_map):
		attendance_register = []
		if emp.get('is_attendance_base') > 0:
			late, overtime, undertime, absent, nightdiff, work_days, absent_days = 0, 0, 0, 0, 0, 0, 0
			unpaid_holiday, prev_lwop, prev_absent  =  0, 0 ,0
			attendance = frappe.db.sql("""SELECT * FROM `tabAttendance Register` 
				WHERE employee = %s AND target_date >= %s AND target_date <= %s""",(emp['name'], add_days(self.period_from, -1), self.period_to), as_dict=1)

			for at in attendance:
				if at.target_date == add_days(self.period_from, -1):
					prev_lwop = 1 if at.is_lwop else 0
					prev_absent = 1 if at.is_absent else 0


				if at.target_date != add_days(self.period_from, -1): 
					if (emp.get("rate_type") == "Daily Rate" and at.is_holiday == 1 and at.is_absent != 1):
						work_days += 0
					elif not at.is_restday:
						work_days += 1

					if at.late > 0:
						late += flt(at.late, 8) * flt(rates.get('hourly_rate'), 8)
					
					if at.undertime > 0:
						undertime += flt(at.undertime, 8) * flt(rates.get('hourly_rate'), 8)

					if at.overtime > 0:
						is_saturday = 1 if getdate(at.target_date).weekday() == 5 else 0
						is_sunday = 1 if getdate(at.target_date).weekday() == 6 else 0
						is_excess = 1 if at.overtime > 8 else 0
						is_db_holiday = 0

						#[RD][HO][SHO][DHO][SUN][SAT][EX]
						overtime_type = [at.is_restday, at.is_holiday, at.is_sp_holiday, is_db_holiday, is_sunday, is_saturday, is_excess]
						overtime_type = ''.join(str(x) for x in overtime_type)

						if overtime_type in ot_map:
							overtime += at.overtime * rates.get('hourly_rate') * (ot_map[overtime_type]['rate'] / 100)
						else:
							overtime += at.overtime * rates.get('hourly_rate')
					
					if ( at.is_absent == 1 or at.is_lwop == 1 ) and not at.is_holiday:
						absent += (emp.get('no_hours') * flt(rates.get('hourly_rate'), 8) ) / 2 if at.is_halfday == 1 else emp.get('no_hours') * flt(rates.get('hourly_rate'), 8)
						absent_days += 0.5 if at.is_halfday == 1 else 1

					if at.is_holiday == 1 and (prev_lwop == 1 or prev_absent == 1 ) and not at.is_ob:
						unpaid_holiday += emp['no_hours'] * flt(rates.get('hourly_rate'), 8)

					#check if this attendance is lwop or absent for next attendance
					prev_lwop = 1 if at.is_lwop else 0
					prev_absent = 1 if at.is_absent else 0

			#Daily rate should have no absent
			if emp.get("rate_type") == "Daily Rate":
				absent = 0
				
			attendance_register.append({"pay_code": "AT", "amount": flt(absent, 8) })
			#attendance_register.append({"pay_code": "UHO", "amount": flt(unpaid_holiday, 8) })
			attendance_register.append({"pay_code": "OT", "amount": flt(overtime, 8) })
			attendance_register.append({"pay_code": "LT", "amount": flt(late, 8) })
			attendance_register.append({"pay_code": "UT", "amount": flt(undertime, 8) })
		
			for d in attendance_register:
				register.append(d)

			header['work_days'] = work_days
			header['absent_days'] = absent_days
			header['present_days'] = work_days - absent_days

	def get_transaction_map(self):
		tr_map = {}
		tr = frappe.db.sql("""SELECT code, title, type, entry_type, account, is_taxable, is_bonus, is_government, is_standard, is_active FROM `tabTransaction Type` """, as_dict=1)
		for t in tr:
			tr_map[t.code] = {"code": t.code, "title": t.title, "type": t.type, "entry_type": t.entry_type,	"account": t.account, 
				"is_taxable": t.is_taxable, "is_standard": t.is_standard, "is_active": t.is_active, "is_bonus": t.is_bonus, "is_government": t.is_government,
			}
		return tr_map

	def get_overtime_map(self):
		ot_map = {}
		ot = frappe.db.sql(""" SELECT ot_code, ot_rate FROM `tabOvertime Rates` """, as_dict=1)
		for t in ot:
			ot_map[t.ot_code] = {
				"rate": t.ot_rate,
			}
		return ot_map

	def get_previous_period(self):
		before = frappe.db.sql_list(""" SELECT `name` FROM `tabPayroll Period` WHERE company = %s 
			AND `schedule` = %s AND payroll_date < %s ORDER BY payroll_date DESC LIMIT 1 """,(self.company, self.schedule, self.payroll_date ))
		previous_period = before[0] if before else ""
		return previous_period

	def get_previous(self, emp, header):
		previous = frappe.db.sql(""" SELECT government_basis, taxable_income, gross_payroll, present_days, work_days, absent_days FROM `tabPayroll Register` 
		WHERE period = %s AND employee = %s LIMIT 1 """,(header.get('previous_period'), emp.get('name')), as_dict=True)		
		for d in previous:
			header['previous_taxable_income'] = d.taxable_income if d.taxable_income else 0
			header['previous_gross_payroll'] = d.gross_payroll if d.gross_payroll else 0
			header['previous_present_days'] = d.present_days if d.present_days else 0
			header['previous_work_days'] = d.work_days if d.work_days else 0
			header['previous_absent_days'] = d.absent_days if d.absent_days else 0
			header['previous_government_basis'] = d.government_basis if d.government_basis else 0

	def create_log(self, ss_list):
		log = "<p>" + _("No Employee for the above selected criteria Payroll or Already Created") + "</p>"
		if ss_list:
			log = "<b>" + _("Payroll Registers Created") + "</b>\
			<br><br>%s" % '<br>'.join(self.format_as_links(ss_list))
		return log

	def format_as_links(self, ss_list):
		return ['<a href="#Form/Salary Slip/{0}">{0}</a>'.format(s) for s in ss_list]