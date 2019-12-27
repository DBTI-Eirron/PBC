# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document
from workwise.payroll.payroll_utils import get_transaction_map, get_overtime_map, get_adjustment_settings, get_rates
from workwise.time_keeping.application_utils import validate_inactive_employee

class SpecialProcessing(Document):
	def get_employees(self):
		employees = frappe.db.sql("""SELECT TE.`name`, TE.full_name, TE.location, TE.company, TE.total_yr_days, 
			TE.rate_type, TE.rate, TE.payroll_schedule, TE.min_take_home, TE.cost_center, TE.no_hours, TE.sss_mode, TE.sss_manual, 
			TE.sss_freq, TE.phic_mode, TE.phic_manual, TE.phic_freq, TE.hdmf_mode, TE.hdmf_manual, TE.hdmf_freq, TE.whtax_mode, 
			TE.whtax_manual, TE.whtax_freq, TE.is_attendance_base, TE.ignore_late, TE.on_hold
			FROM `tabEmployee` TE LEFT JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name`
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
				"period_group": self.period_group,
			}), as_dict=True)

		return employees

	def get_conditions(self):
		conditions = []
		strict_period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')

		if frappe.session.user != "Administrator":
			conditions.append(_("TE.sensitivity IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

		if self.employee:
			conditions.append("TE.`name`=%(employee)s")

		if strict_period_group:
			conditions.append("TE.period_group=%(period_group)s")

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

	def validate_employee(self):
		if self.employee:
			validate_inactive_employee(self)
			em_period_group = frappe.db.get_value("Employee", self.employee, "period_group")
			if self.period_group != em_period_group:
				frappe.throw(_("Employee does not belong to Period Group"))
 
	def process_special(self):
		self.validate_employee()
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
			"Special Period": self.special_period,
		}

		func = switcher.get(self.method, lambda: frapp.throw(_("Invalid Method")))
		func(header, entries)

		if self.method not in ["Special Period"]:
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

	def special_period(self, header, entries):
		status, is_special = frappe.db.get_value("Payroll Period", self.period, ["status","is_special"])
		if status == "Closed":
			frappe.throw(_("Selected Period is Already Closed"))

		if not is_special:
			frappe.throw(_("Selected Period must be Special"))

		ss_list = []
		employees = self.get_employees()
		tr_map = get_transaction_map()
		ot_map = get_overtime_map()
		adj_settings = None
		uho_ab_days = frappe.db.get_single_value('Payroll Settings', 'uho_ab_days')
		uho_ab_spnw = frappe.db.get_single_value('Payroll Settings', 'uho_ab_spnw')
		lwop_uho = frappe.db.get_single_value('Payroll Settings', 'hd_lwop_as_uho')
		ex_uho_spnw = frappe.db.get_single_value('Payroll Settings', 'ex_uho_spnw')
		weekly_prev_map = None
		weekly_set = None
		previous_period = None
		no_weeks = None
		
		if employees:
			no_emp = len(employees)
			proc_emp = 0
			for emp in employees:
				frappe.db.sql("""DELETE FROM `tabPayroll Register` WHERE employee = %s AND period = %s """,(emp.name, self.period ), as_dict=1)
				register = []
				header = {
					'employee': emp.name,
					'employee_name': emp.full_name,
					'company': emp.company,
					'on_hold': emp.on_hold,
					'location': emp.location,
					'posting_date': self.payroll_date,
					'process_date': nowdate(),
					'period': self.period,
					'weekly_set': weekly_set,
					'no_weeks': no_weeks,
					'schedule': self.schedule,
					'frequency': "Special",
					'previous_period': previous_period,
					'previous_taxable_income': 0.0,
					'previous_work_days': 0.0,
					'previous_absent_days': 0.0,
					'previous_present_days': 0.0,
					'previous_gross_payroll': 0.0,
					'previous_government_basis': 0.0,
					'prev_govt_deduction':0.0,
					'prev_govt_income': 0.0,
					'bonus_income': 0.0,
					'bonus_deduction': 0.0,
					'taxable_income': 0.0,
					'taxable_deduction': 0.0,
					'total_income': 0.0,
					'total_deduction': 0.0,
					'government_basis': 0.0,
					'govt_income': 0.0,
					'govt_deduction': 0.0,
					'work_days': 0.0,
					'absent_days': 0.0,
					'present_days': 0.0,
					'net_payroll': 0.0,
					'gross_payroll': 0.0,
					'bonus': 0.0,
					'is_special': 1,
					#Payroll Settings
					'uho_ab_days': uho_ab_days,
					'uho_ab_spnw': uho_ab_spnw,
					'lwop_uho': lwop_uho,
					'ex_uho_spnw': ex_uho_spnw
				}

				#Calculate Rates and Previous Entries
				rates = get_rates(emp)
				#Calculate Basic Entries
				self.get_recurring(emp, rates, header, register)
				self.get_batch(emp, rates, header, register)

				#Calculate Basic Entries to Header
				self.calculate_basic_header(register, header, tr_map)
				self.get_whtax(emp, rates, header, register)
				#Calculate Totals
				self.calculate_payroll_totals(header)
				self.calculate_rates_header(header, rates)
				
				#Make Entry
				if header.get('net_payroll') > 0:
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
						proc_emp += 1

					payslip_label = " " + emp.full_name +""
					if emp.on_hold:
						payslip_label += " <span class='label label-danger'> On-Hold </span>"
					ss_list.append(payslip_label)

			ss_list.append("<b>Processed "+ str(proc_emp)+" / "+str(no_emp)+" Employees</b>")
		else:
			frappe.throw(_("No Employee Found"))

	def get_assumed_cutoff_amt(self, monthly_rate, no_weeks):
		assumed_bonus = 0
		if self.schedule == "Semi-Monthly":
			if cint(self.assume_cutoffs) == 1:
				assumed_bonus = monthly_rate / 2

		elif self.schedule == "Weekly":
			assumed_weekly_amt = monthly_rate / cint(no_weeks)
			assumed_bonus = assumed_weekly_amt * cint(self.assume_cutoffs)

		return assumed_bonus


	def bonus_pay(self, header, entries):
		bonus_transaction = frappe.db.get_single_value("Payroll Settings", "bonus_transaction") 
		if not bonus_transaction:
			frappe.throw(_("No Default Bonus Transaction Type"))
		header['transaction_type'] = bonus_transaction
		header['remarks'] = ("13th month pay for year {0}").format(self.payroll_year)

		#validate assume cutoffs:
		no_weeks = 0
		if cint(self.assume_cutoffs) in [1,2,3,4]:
			if self.schedule == "Monthly":
				frappe.throw(_("Assume Cutoffs not Allowed for Monthly"))

			if self.schedule == "Semi-Monthly":
				if cint(self.assume_cutoffs) in [2,3,4]:
					frappe.throw(_("Assume Cutoffs 2,3,4 not Allowed for Semi-Monthly"))

			if self.schedule == "Weekly":
				weekly_set = frappe.db.get_value("Payroll Period", self.period, ["weekly_set"])
				if weekly_set:
					no_weeks = frappe.db.get_value("Weekly Set", weekly_set, ["no_weeks"])
					if cint(no_weeks) == 4:
						if cint(self.assume_cutoffs) in [4]:
							frappe.throw(_("Assume Cutoffs 4 not Allowed for Weekly with {0} no. of weeks").format(no_weeks))

		bonus_method = frappe.db.get_single_value("Payroll Settings", "bonus_method") 
		from_year, to_year = frappe.db.get_value("Payroll Year", self.payroll_year, ["from_date", "to_date"])
		employees = self.get_employees()
		if employees:
			for emp in employees:
				rates = get_rates(emp)
				total_bonus = 0
				if bonus_method == "Standard":
					registerx = frappe.db.sql(""" SELECT PRE.`name`, PRE.`pay_code`, PRE.`amount`
						FROM `tabPayroll Register Entries` PRE 
						INNER JOIN `tabPayroll Register` PR ON PRE.`parent`=PR.`name`
						WHERE PRE.`pay_code` = 'BS' AND PR.`employee` = %(employee)s 
						AND PR.`posting_date` >= %(from_year)s AND PR.`posting_date` <= %(to_year)s AND is_special = 0  """,{ 
						"employee": emp.name,
						"from_year": from_year,
						"to_year": to_year,
					}, as_dict=True)

					for d in registerx:
						if d.pay_code == 'BS':
							total_bonus += d.amount

					if self.assume_last_month:
						if self.assume_cutoffs:
							total_bonus += self.get_assumed_cutoff_amt(rates.get('monthly_rate'), no_weeks)
						else:
							total_bonus += rates.get('monthly_rate')

					total_bonus = total_bonus / 12

				elif bonus_method == "Bonus Basis":
					bonus_basis = frappe.db.sql(""" SELECT bonus FROM `tabPayroll Register` WHERE employee = %(employee)s 
						AND posting_date >= %(from_year)s AND posting_date <= %(to_year)s AND is_special = 0 """,{ 
							"employee": emp.name,
							"from_year": from_year,
							"to_year": to_year,
					}, as_dict=True)

					for d in bonus_basis:
						total_bonus += d.bonus

					if self.assume_last_month:
						if self.assume_cutoffs:
							total_bonus += self.get_assumed_cutoff_amt(rates.get('monthly_rate'), no_weeks)
						else:
							total_bonus += rates.get('monthly_rate')					

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
						WHERE PR.`employee` = %(employee)s AND PR.`posting_date` >= %(from_year)s AND PR.`posting_date` <= %(to_year)s AND PR.is_special = 0  """,{ 
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

					if self.assume_last_month:
						if self.assume_cutoffs:
							#frappe.throw(_(self.get_assumed_cutoff_amt(rates.get('monthly_rate'), no_weeks)))
							total_bonus += self.get_assumed_cutoff_amt(rates.get('monthly_rate'), no_weeks)
						else:
							#frappe.throw(_("{0} {1}").format(rates.get('monthly_rate'), total_bonus))
							total_bonus += rates.get('monthly_rate')

					total_bonus = total_bonus / 12

				entries.append({
					"employee": emp.name,
					"employee_name": emp.full_name, 
					"amount": total_bonus,
				})

		return header, entries

	def leave_to_cash(self, header, entries):
		header['transaction_type'] = self.convert_to
		header['remarks'] = ("Leave to cash for year {0}").format(self.payroll_year)

		bonus_method = frappe.db.get_single_value("Payroll Settings", "bonus_method") 
		from_year, to_year = frappe.db.get_value("Payroll Year", self.payroll_year, ["from_date", "to_date"])
		employees = self.get_employees()
		if employees:
			for emp in employees:
				rates = get_rates(emp)
				total_amt = 0
				registerx = frappe.db.sql(""" SELECT credits, used_credits FROM `tabLeave Balance` 
					WHERE employee = %(employee)s
					AND leave_type =  %(lv_convert)s
					AND from_date >= %(from_year)s 
					AND to_date <= %(to_year)s """,{ 
						"employee": emp.name,
						"from_year": from_year,
						"to_year": to_year,
						"schedule": emp.payroll_schedule,
						"lv_convert": self.lv_convert,
				}, as_dict=True)

				total_credits = 0.0
				for d in registerx:
					credits = 0
					credits = d.credits - d.used_credits
					if credits > 0:
						total_credits += credits

				total_amt = credits * rates.get('daily_rate')
				entries.append({
					"employee": emp.name,
					"employee_name": emp.full_name, 
					"amount": total_amt,
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
		log = "<p>" + _("Special Entries created") + "</p>"
		return log

	def get_recurring(self, emp, rates, header, register):
		recurring_register = []
		recurring = frappe.db.sql("""SELECT RE.`name`, RE.method, REE.amount, RE.transaction_type, RE.frequency FROM `tabRecurring Entry` RE
			INNER JOIN `tabRecurring Entry Employees` REE ON RE.`name` = REE.parent WHERE REE.employee = %s 
			AND RE.status = 'Enabled' AND RE.company = %s AND is_special = 1 AND RE.docstatus < 2 """,(emp['name'], self.company), as_dict=True )
		
		for rec in recurring :
			if self.frequency == rec.frequency or rec.frequency == 'Both':
				if rec.frequency == 'Both':
					amt = flt(rec.amount, 8) / 2
				else:
					amt = rec.amount
				
				if rec.method == "Present Days":
					amt = flt(amt * header.get('present_days'), 8)

				elif rec.method == 'Work Days':
					amt = flt(amt * header.get('work_days'), 8)
	
				elif rec.method == 'Deduct Absent':
					hourly_rate = self.get_hourly_rate_base(amt, emp)
					amt = (amt - (( header.get('absent_days') * 8) * hourly_rate * 2))

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
				amt = (amt - (( header.get('absent_days') * 8) * hourly_rate * 2))

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
						if not d.get("pay_code") == "BS":
							header['prev_govt_income'] += d.get('amount')

				elif tr_map[d.get("pay_code")]['type'] == 'Deduction':
					header['total_deduction'] += d.get('amount')
					
					if tr_map[d.get("pay_code")]['is_taxable']:
						header['taxable_deduction'] += d.get('amount')

					if tr_map[d.get("pay_code")]['is_bonus']:
						header['bonus_deduction'] += d.get('amount')

					if tr_map[d.get("pay_code")]['is_government']:
						header['government_basis'] -= d.get('amount')
						header['prev_govt_deduction'] += d.get('amount')
	
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

	def get_whtax(self, emp, rates, header, register):
		taxable = flt(header.get('taxable_income'), 8) - flt(header.get('taxable_deduction'), 8)
		tax_amt = 0
		
		if emp['whtax_mode'] != "None":
			if emp.get('payroll_schedule') == 'Semi-Monthly':
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
			header['total_deduction'] += flt(tax_amt, 8)
