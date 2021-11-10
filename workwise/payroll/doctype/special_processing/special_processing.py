# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from frappe.model.document import Document
from workwise.payroll.payroll_utils import get_transaction_map, get_overtime_map, get_adjustment_settings, get_rates, get_hdmf_table, get_sss_table, get_sss_amount, get_hdmf_amount
from workwise.time_keeping.application_utils import validate_inactive_employee
#from workwise.payroll.doctype.payroll_processing.payroll_processing import get_sss, get_phic, get_hdmf
from workwise.payroll.weekly_utils import get_weekly_prev_map, get_weekly_basis

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

	def validate_fields(self):
		if self.method == 'Leave Balance to Cash':
			if not self.lv_convert:
				frappe.throw(_("Convert Leave Type is required"))

			if not self.convert_to:
				frappe.throw(_("Converted Transaction Type is required"))

			
			if not frappe.db.get_value("Leave Type", self.lv_convert, "convertible"):
				frappe.throw(_("Leave Type is not convertible"))
 
	def process_special(self):
		self.validate_employee()
		self.validate_period()
		self.validate_fields()
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
		if self.method in ['No Work']:
			header["method"] = self.method

		switcher = {
			"13th Month": self.bonus_pay,
			"Leave Balance to Cash": self.leave_to_cash,
			"Special Period": self.special_period,
			"No Work": self.special_period,
		}

		func = switcher.get(self.method, lambda: frapp.throw(_("Invalid Method")))
		func(header, entries)

		if self.method not in ["Special Period", "No Work"]:
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

		if header.get("method") not in ["No Work"]:
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
		sss_table = None
		hdmf_table = None
		previous_period = self.get_previous_period()

		if header.get("method") in ["No Work"]:
			sss_table = get_sss_table()
			hdmf_table = get_hdmf_table()
			weekly_prev_map = frappe._dict()
			if self.schedule == "Weekly":
				weekly_prev_map = get_weekly_prev_map(employees, weekly_set)

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
					'sss_inc': 0.0,
					'sss_ded': 0.0,
					'sss_amt': 0.0,
					'sss_er_amt': 0.0,
					'sss_ec_amt': 0.0,
					'sss_er_mpf': 0.0,
					'sss_ee_mpf': 0.0,
					'phic_inc': 0.0,
					'phic_ded': 0.0,
					'phic_amt': 0.0,
					'phic_er_amt': 0.0,
					'phic_ec_amt': 0.0,
					'hdmf_inc': 0.0,
					'hdmf_ded': 0.0,
					'hdmf_amt': 0.0,
					'hdmf_er_amt': 0.0,
					'hdmf_ec_amt': 0.0,
					'hdmf_manual': 0.0,
					'whtax_amt': 0.0,
					'govt_basic': 0.0,
					'hourly_basic': 0.0,
					#previous cutoff Data
					'prev_govt_basic': 0.0,
					'prev_sss_inc': 0.0,
					'prev_sss_ded': 0.0,
					'prev_sss_amt': 0.0,
					'prev_sss_er_amt': 0.0,
					'prev_sss_ec_amt': 0.0,
					'prev_sss_ee_mpf': 0.0,
					'prev_sss_er_mpf': 0.0,
					'prev_phic_inc': 0.0,
					'prev_phic_ded': 0.0,
					'prev_phic_amt': 0.0,
					'prev_phic_er_amt': 0.0,
					'prev_phic_ec_amt': 0.0,
					'prev_hdmf_inc': 0.0,
					'prev_hdmf_ded': 0.0,
					'prev_hdmf_amt': 0.0,
					'prev_hdmf_er_amt': 0.0,
					'prev_hdmf_ec_amt': 0.0,
					'prev_hdmf_manual': 0.0,
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
					'ex_uho_spnw': ex_uho_spnw
				}

				#Calculate Rates and Previous Entries
				rates = get_rates(emp)
				if self.method in ["No Work"]:
					self.get_previous(emp, header)
				#Calculate Basic Entries
				self.get_recurring(emp, rates, header, register)
				self.get_batch(emp, rates, header, register)
				if self.method in ["No Work"]:
					#Overwrite BS
					batch_bs = list(filter(lambda x: x['pay_code'] == 'BS' and x['linked_doctype'] == 'Batch Entry', register))
					if batch_bs and batch_bs[0].get("amount"):
						rates = get_rates(emp, flt(batch_bs[0].get("amount"), 8))
				#Calculate Basic Entries to Header
				self.calculate_basic_header(register, header, tr_map)
				if self.method in ["No Work"]:
					self.get_sss(emp, rates, header, register, tr_map, sss_table, weekly_prev_map)
					self.get_phic(emp, rates, header, register, tr_map, weekly_prev_map)
					self.get_hdmf(emp, rates, header, register, tr_map, hdmf_table, weekly_prev_map)
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

				valid_entry = {}
				less_entry = {}
				total_balance = 0
				lb_entries = frappe.db.sql(""" SELECT * FROM `tabLB Entry` WHERE `employee` = %s AND `leave_type` = %s ORDER BY `from_date` ASC """, (emp.name, self.lv_convert), as_dict=1)
				for d in lb_entries:
					if d.balance_type == "Add":
						if d.name not in valid_entry:
							valid_entry[d.name] = {
								"credits": d.credits,
								"from": getdate(d.from_date),
								"to": getdate(d.to_date),
							}
					else:
						if d.name not in less_entry:
							less_entry[d.name] = {
								"used": 0,
								"credits": d.credits,
								"from": getdate(d.from_date),
								"to": getdate(d.to_date),
							}

				for vl in valid_entry:
					to_less = 0
					for le in less_entry:
						if valid_entry[vl]['credits'] > 0 and not less_entry[le]['used']:
							if ( valid_entry[vl]['from'] <= less_entry[le]['from'] <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= less_entry[le]['to'] <= valid_entry[vl]['to'] ):
								to_less += less_entry[le]['credits']
								less_entry[le]['used'] = 1
					valid_entry[vl]['credits'] -= to_less
					if ( valid_entry[vl]['from'] <= getdate(from_year) <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= getdate(to_year) <= valid_entry[vl]['to'] ):
						total_balance += valid_entry[vl]['credits']
				
				if total_balance <= 0:
					total_balance = 0

				total_amt = total_balance * rates.get('daily_rate')
				entries.append({
					"employee": emp.name,
					"employee_name": emp.full_name, 
					"amount": total_amt,
				})

		return header, entries

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

					if d.get("pay_code") == "BS":
						header['govt_basic'] += d.get('amount')
					
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

	def get_sss(self, emp, rates, header, register, tr_map, sss_table, weekly_prev_map):
		sss_register = []
		
		if emp.get('sss_mode') != "None":
			sss_register = []
			sss_list = ["sss","ssse","sssc", "ssseempf", "sssermpf"]
			sss, ssse, sssc, ssseempf, sssermpf = 0, 0, 0, 0, 0
			target_amt = 0

			if emp.get('payroll_schedule') == "Monthly" and self.schedule == emp['payroll_schedule']:
				if self.frequency == '2nd' and emp.get('sss_freq') == '2nd':
					target_amt = header.get('govt_basic') + header.get('sss_inc') - header.get('sss_ded')

					if emp.get("rate_type") == "Daily Rate" and header.get('mo_amt_smdl') and header.get('sss_smdl'):
						target_amt = rates.get('monthly_rate') + header.get('sss_inc') - header.get('sss_ded')

					if header.get("govt_use_old"):
						target_amt = (rates.get('monthly_rate') + flt(header.get('sss_inc'), 8)) - flt(header.get('sss_ded'), 8)

			if emp.get('payroll_schedule') == "Semi-Monthly" and self.schedule == emp['payroll_schedule']:
				if self.frequency == emp.get('sss_freq') or emp.get('sss_freq') in ['Both', 'All']:
					target_amt = header.get('prev_govt_basic') + header.get('govt_basic') + \
						(header.get('prev_sss_inc') + header.get('sss_inc')) - (header.get('prev_sss_ded') + header.get('sss_ded'))

					if header.get("govt_use_old"):
						target_amt = (rates.get('monthly_rate') + flt(header.get('sss_inc'), 8)) - flt(header.get('sss_ded'), 8) 

					if emp.get('sss_freq') == '1st' and emp.get("rate_type") != "Daily Rate":
						target_amt = rates.get('monthly_rate') + header.get('sss_inc') - header.get('sss_ded')

					if emp.get('sss_freq') == '2nd' and emp.get("rate_type") != "Daily Rate":
						if header.get('prev_monthly_rate') != rates.get('monthly_rate') and header.get('prev_monthly_basis') > 0:
							target_amt = (rates.get('monthly_rate') / 2)+ \
								(header.get('prev_sss_inc') + header.get('sss_inc')) - (header.get('prev_sss_ded') + header.get('sss_ded'))

						if header.get("govt_use_old"):
							target_amt = (rates.get('monthly_rate') + flt(header.get('prev_sss_inc'), 8)) - flt(header.get('prev_sss_ded'), 8)

					if emp.get("rate_type") == "Daily Rate" and header.get('mo_amt_smdl') and header.get('sss_smdl'):
						target_amt = rates.get('monthly_rate') + (header.get('prev_sss_inc') + header.get('sss_inc')) - (header.get('prev_sss_ded') + header.get('sss_ded'))
						if self.frequency == '1st' and emp.get('sss_freq') in ['Both', 'All']:
							target_amt = (rates.get('monthly_rate')/2) + header.get('sss_inc') - header.get('sss_ded')

					if emp.get('sss_mode') == "ME Table":
						target_amt = rates.get('monthly_rate')

			if emp.get('payroll_schedule') == "Weekly" and self.schedule == emp['payroll_schedule']:
				if emp.get('sss_mode') == "ME Table":
					if emp.get('sss_freq') == "1st" and self.frequency == "2nd":
						target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

					if emp.get('sss_freq') == "2nd" and self.frequency in ["4th", "5th"]:
						if cint(header.get("no_weeks")) == cint(5):
							if self.frequency in ["2nd", "5th"]:
								target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

						if cint(header.get("no_weeks")) == cint(4):
							if self.frequency in ["2nd", "4th"]:
								target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

					if emp.get('sss_freq') == 'Both':
						if cint(header.get("no_weeks")) == cint(5):
							if self.frequency in ["2nd", "5th"]:
								target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

						if cint(header.get("no_weeks")) == cint(4):
							if self.frequency in ["2nd", "4th"]:
								target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

					if emp.get('sss_freq') == 'All':
						freq_all_passed = 0
						if cint(header.get("no_weeks")) == cint(1):
							if self.frequency in ['1st']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(2):
							if self.frequency in ['1st', '2nd']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(3):
							if self.frequency in ['1st', '2nd', '3rd']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(4):
							if self.frequency in ['1st', '2nd', '3rd', '4th']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(5):
							if self.frequency in ['1st', '2nd', '3rd', '4th', '5th']:
								freq_all_passed = 1

						if freq_all_passed:
							target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12
				else:
					weekly_govt_basis = (header.get('govt_basic') + header.get('sss_inc')) - header.get('sss_ded')
					target_amt, monthly_basis, weekly_previous_amts = get_weekly_basis('sss', emp, header, emp.get('sss_freq'), self.frequency, weekly_prev_map, flt(weekly_govt_basis, 8) )
					#update previous amounts based on weekly set data
					header['prev_sss_amt'] = weekly_previous_amts['sss']
					header['prev_sss_er_amt'] = weekly_previous_amts['ssse']
					header['prev_sss_ec_amt'] = weekly_previous_amts['sssc']
					header['prev_sss_er_mpf'] = weekly_previous_amts['sss_er_mpf']
					header['prev_sss_ee_mpf'] = weekly_previous_amts['sss_ee_mpf']

			if target_amt and emp.get('sss_mode') != "None":
				#Round target_amt to against SSS table
				sss, ssse, sssc, ssseempf, sssermpf = get_sss_amount(flt(target_amt, 2), sss_table)

				if emp.get('sss_mode') == "Manual" and emp.get('sss_manual'):
					ssse, sssc, ssseempf, sssermpf = 0, 0, 0, 0
					sss = emp.get('sss_manual')
					if emp.get('payroll_schedule') == "Semi-Monthly" and emp.get('sss_freq') in ["Both", "All"]:
						sss = emp.get('sss_manual') / 2

				for l in sss_list:
					amt = flt(eval(l), 8)

					if emp.get('payroll_schedule') in ["Semi-Monthly"] and emp.get('sss_freq') == "Both" and emp.get('sss_mode') == "ME Table":
						if self.frequency != '2nd':
							amt = abs(flt(eval(l), 8) / 2)

					if emp.get('payroll_schedule') in ["Weekly"] and emp.get('sss_freq') in ["All"] and emp.get('sss_mode') == "ME Table":
						amt = abs(flt(eval(l), 8) / cint(header.get("no_weeks")))

					if emp.get('payroll_schedule') in ["Weekly"] and emp.get('sss_freq') in ["Both"] and emp.get('sss_mode') == "ME Table":
						amt = abs(flt(eval(l), 8) / 2)

					if emp.get('sss_mode') != "Manual":
						#For EE
						if l.upper() == 'SSS' and header.get('prev_sss_amt') and emp.get('sss_freq') in ["Both", "All"]:
							amt = amt - header.get('prev_sss_amt')
							if amt < 1:
								amt = 0

						#For ER
						if l.upper() == 'SSSE' and header.get('prev_sss_er_amt') and emp.get('sss_freq') in ["Both", "All"]:
							amt = amt - header.get('prev_sss_er_amt')
							if amt < 1:
								amt = 0

						#For EC
						if l.upper() == 'SSSC' and header.get('prev_sss_ec_amt') and emp.get('sss_freq') in ["Both", "All"]:
							amt = amt - header.get('prev_sss_ec_amt')
							if amt < 1:
								amt = 0

						if l.upper() == 'SSSC':
							if frappe.db.get_single_value('Payroll Settings', 'sss_ec_deduct_last'):
								if emp.get('sss_mode') == "Table" and emp.get('payroll_schedule') in ["Weekly"] and emp.get('sss_freq') in ["All"]:
									if self.frequency not in [str(cint(header.get("no_weeks")))+'th']:
										amt = 0

						#For MPF Employer
						if l.upper() == 'SSSERMPF' and header.get('prev_sss_er_mpf') and emp.get('sss_freq') in ["Both", "All"]:
							amt = amt - header.get('prev_sss_er_mpf')
							if amt < 1:
								amt = 0

						#For MPF Employee
						if l.upper() == 'SSSEEMPF' and header.get('prev_sss_ee_mpf') and emp.get('sss_freq') in ["Both", "All"]:
							amt = amt - header.get('prev_sss_ee_mpf')
							if amt < 1:
								amt = 0	

					sss_register.append({"pay_code": l.upper(), "amount": amt })

		if emp.get('sss_mode') != "None":
			for d in sss_register:
				register.append(d)
				if d.get('pay_code') == "SSS" and d.get('amount') > 0:
					header['sss_amt'] = d.get('amount')

				if d.get('pay_code') == "SSSE" and d.get('amount') > 0:
					header['sss_er_amt'] = d.get('amount')

				if d.get('pay_code') == "SSSC" and d.get('amount') > 0:
					header['sss_ec_amt'] = d.get('amount')

				if d.get('pay_code') == "SSSEEMPF" and d.get('amount') > 0:
					header['sss_ee_mpf'] = d.get('amount')

				if d.get('pay_code') == "SSSERMPF" and d.get('amount') > 0:
					header['sss_er_mpf'] = d.get('amount')

				self.calculate_special_header(d, header, tr_map)

	def get_phic(self, emp, rates, header, register, tr_map, weekly_prev_map):
		phic_register = []
		if emp.get('phic_mode') != "None":
			phic_register = []
			phic_list = ["phic","phice"]
			manual = flt(emp.get("phic_manual"), 8)
			mode = emp.get('phic_mode')
			target_amt = 0

			if emp.get('payroll_schedule') == "Monthly" and self.schedule == emp['payroll_schedule']:
				if self.frequency == '2nd' and emp.get('phic_freq') == '2nd':
					target_amt = header.get('govt_basic') + header.get('phic_inc') - header.get('phic_ded')

					if emp.get("rate_type") == "Daily Rate" and header.get('mo_amt_smdl') and header.get('phic_smdl'):
						target_amt = rates.get('monthly_rate') + header.get('phic_inc') - header.get('phic_ded')

					if header.get("govt_use_old"):
						target_amt = (rates.get('monthly_rate') + flt(header.get('phic_inc'), 8)) - flt(header.get('phic_ded'), 8)

			if emp.get('payroll_schedule') == "Semi-Monthly" and self.schedule == emp['payroll_schedule']:
				if self.frequency == emp.get('phic_freq') or emp.get('phic_freq') in ['Both', 'All']:
					target_amt = header.get('prev_govt_basic') + header.get('govt_basic') + \
						(header.get('prev_phic_inc') + header.get('phic_inc')) - (header.get('prev_phic_ded') + header.get('phic_ded'))

					if header.get("govt_use_old"):
						target_amt = (rates.get('monthly_rate') + flt(header.get('phic_inc'), 8)) - flt(header.get('phic_ded'), 8) 

					if emp.get('phic_freq') == '1st' and emp.get("rate_type") != "Daily Rate":
						target_amt = rates.get('monthly_rate') + header.get('phic_inc') - header.get('phic_ded')

					if emp.get('phic_freq') == '2nd' and emp.get("rate_type") != "Daily Rate":
						if header.get('prev_monthly_rate') != rates.get('monthly_rate') and header.get('prev_monthly_basis') > 0:
							target_amt = (rates.get('monthly_rate') / 2)+ \
								(header.get('prev_phic_inc') + header.get('phic_inc')) - (header.get('prev_phic_ded') + header.get('phic_ded'))

						if header.get("govt_use_old"):
							target_amt = (rates.get('monthly_rate') + flt(header.get('prev_phic_inc'), 8)) - flt(header.get('prev_phic_ded'), 8)

					if emp.get("rate_type") == "Daily Rate" and header.get('mo_amt_smdl') and header.get('phic_smdl'):
						target_amt = rates.get('monthly_rate') + (header.get('prev_phic_inc') + header.get('phic_inc')) - (header.get('prev_phic_ded') + header.get('phic_ded'))
						if self.frequency == '1st' and emp.get('phic_freq') in ['Both', 'All']:
							target_amt = (rates.get('monthly_rate')/2) + header.get('phic_inc') - header.get('phic_ded')

					if emp.get('phic_mode') == "ME Table": #and self.frequency == '2nd':
						target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12
						
					if header.get('phic_mo_basis') and emp.get('phic_freq') == 'Both':
						target_amt = rates.get('monthly_rate')

			if emp.get('payroll_schedule') == "Weekly" and self.schedule == emp['payroll_schedule']:
				if emp.get('phic_mode') == "ME Table":
					if emp.get('phic_freq') == "1st" and self.frequency == "2nd":
						target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

					if emp.get('phic_freq') == "2nd" and self.frequency in ["4th", "5th"]:
						if cint(header.get("no_weeks")) == cint(5):
							if self.frequency in ["2nd", "5th"]:
								target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

						if cint(header.get("no_weeks")) == cint(4):
							if self.frequency in ["2nd", "4th"]:
								target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

					if emp.get('phic_freq') == 'Both':
						if cint(header.get("no_weeks")) == cint(5):
							if self.frequency in ["2nd", "5th"]:
								target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

						if cint(header.get("no_weeks")) == cint(4):
							if self.frequency in ["2nd", "4th"]:
								target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

					if emp.get('phic_freq') == 'All':
						freq_all_passed = 0
						if cint(header.get("no_weeks")) == cint(1):
							if self.frequency in ['1st']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(2):
							if self.frequency in ['1st', '2nd']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(3):
							if self.frequency in ['1st', '2nd', '3rd']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(4):
							if self.frequency in ['1st', '2nd', '3rd', '4th']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(5):
							if self.frequency in ['1st', '2nd', '3rd', '4th', '5th']:
								freq_all_passed = 1

						if freq_all_passed:
							target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12
				else:
					govt_basis = header.get('govt_basic')
					govt_basis += (header['phic_inc'] - header['phic_ded'])
					target_amt, monthly_basis = get_weekly_basis('phic', emp, header, emp.get('phic_freq'), self.frequency, weekly_prev_map, flt(govt_basis, 8) )
			
			if target_amt and emp.get('phic_mode') != "None":
				phic_min_range = 0
				phic_max_range = 0
				phic_perc = 0
				phic_min_rate = 0
				phic_max_rate = 0
				payroll_year = frappe.get_value("Payroll Period", self.period, "payroll_year")
				phic_table = frappe.db.sql("""SELECT `year`, `minimum`, `premium_rate`, `maximum` FROM `tabPHIC Table` WHERE `year` = %s LIMIT 1""",(payroll_year), as_dict=1 )
				if phic_table:
					phic_min_range = flt(phic_table[0].minimum)
					phic_max_range = flt(phic_table[0].maximum)
					phic_perc = flt(phic_table[0].premium_rate)
					phic_min_rate = flt(phic_table[0].minimum) * ((flt(phic_table[0].premium_rate, 8) / 100) / 2)
					phic_max_rate = flt(phic_table[0].maximum) * ((flt(phic_table[0].premium_rate, 8) / 100) / 2)
				else:
					frappe.throw(_('No PHIC setup for year {0}'.format(payroll_year)))

				phic, phice = 0, 0
				manual = 0
				if emp.get('phic_mode') == "Manual":
					if emp.get('phic_manual'):
						manual = emp.get('phic_manual')
						if emp.get('payroll_schedule') == "Semi-Monthly" and emp.get('phic_freq') in ["Both", "All"]:
							manual = emp.get('phic_manual') / 2

				if target_amt <= phic_min_range:
					phic = manual if mode == "Manual" and manual > phic_min_rate else phic_min_rate
					phice = phic_min_rate

				if phic_min_range < target_amt < phic_max_range:
					rate_value = ( target_amt * (flt(phic_perc, 8) / 100) / 2)
					phic = manual if mode == "Manual" and manual > rate_value else rate_value 
					phice = rate_value

				if target_amt >= phic_max_range:
					phic = manual if mode == "Manual" and manual > phic_max_rate else phic_max_rate
					phice = phic_max_rate

				for l in phic_list:
					amt = flt(eval(l), 8)

					if emp.get('payroll_schedule') == "Semi-Monthly" and emp.get('phic_freq') in ["Both", "All"]:
						if emp.get('phic_mode') == "ME Table":
							amt = abs(flt(eval(l), 8) / 2)

					if emp.get('payroll_schedule') == "Weekly" and emp.get('phic_freq') == "Both":
						if emp.get('phic_mode') == "ME Table":
							if self.frequency == '2nd':
								amt = abs(flt(eval(l), 8) / 2)

						if self.frequency != '2nd':
							if emp.get('phic_mode') == "ME Table":
								samt = abs(flt(eval(l), 8) / 2)

							if weekly_prev_map and emp['name'] in weekly_prev_map:
								prv_phic = filter(lambda dct: dct['frequency'] in ['2nd'], weekly_prev_map[emp['name']]['previous_data'])
								if prv_phic:
									amt = abs(flt(eval(l), 8) - prv_phic[0][l])
								else:
									if emp.get('phic_mode') == "ME Table":
										amt = samt

					if emp.get('payroll_schedule') == "Weekly" and emp.get('phic_freq') == "All":
						if emp.get('phic_mode') == "ME Table":
							amt = flt(eval(l), 8) / cint(header.get("no_weeks"))

						if emp.get('phic_mode') == "Table":
							valid_prev = []
							if self.frequency == "2nd":
								valid_prev = ["1st"]
							if self.frequency == "3rd":
								valid_prev = ["1st", "2nd"]
							if self.frequency == "4th":
								valid_prev = ["1st", "2nd", "3rd"]
							if self.frequency == "5th":
								valid_prev = ["1st", "2nd", "3rd", "4th"]

							amt = abs(flt(eval(l), 8))
							prv_phic = filter(lambda dct: dct['frequency'] in valid_prev, weekly_prev_map[emp['name']]['previous_data'])
							if prv_phic:
								for prv in prv_phic:
									amt = abs(amt - prv[l])

					if emp.get('phic_mode') != "Manual" and emp.get('phic_mode') != "ME Table":
						#For EE
						if l.upper() == 'PHIC' and header.get('prev_phic_amt') and emp.get('phic_freq') in ["Both", "All"]:
							amt = amt - header.get('prev_phic_amt')
							if amt < 1:
								amt = 0

						#For ER
						if l.upper() == 'PHICE' and header.get('prev_phic_er_amt') and emp.get('phic_freq') in ["Both", "All"]:
							amt = amt - header.get('prev_phic_er_amt')
							if amt < 1:
								amt = 0

					phic_register.append({"pay_code": l.upper(), "amount": amt })

		if emp.get('phic_mode') != "None":
			for d in phic_register:
				register.append(d)

				if d.get('pay_code') == "PHIC" and d.get('amount') > 0:
					header['phic_amt'] = d.get('amount')

				if d.get('pay_code') == "PHICE" and d.get('amount') > 0:
					header['phic_er_amt'] = d.get('amount')

				self.calculate_special_header(d, header, tr_map)

	def get_hdmf(self, emp, rates, header, register, tr_map, hdmf_table, weekly_prev_map):
		hdmf_register = []

		if emp.get('hdmf_mode') != "None":
			hdmf_register = []
			hdmf_list = ["hdmf","hdmfe","hdmfm"]
			hdmf, hdmfe, hdmfm = 0, 0, 0
			target_amt = 0

			if emp.get('payroll_schedule') == "Monthly" and self.schedule == emp['payroll_schedule']:
				if self.frequency == '2nd' and emp.get('hdmf_freq') == '2nd':
					target_amt = header.get('govt_basic') + header.get('hdmf_inc') - header.get('hdmf_ded')

					if emp.get("rate_type") == "Daily Rate" and header.get('mo_amt_smdl') and header.get('hdmf_smdl'):
						target_amt = rates.get('monthly_rate') + header.get('hdmf_inc') - header.get('hdmf_ded')

					if header.get("govt_use_old"):
						target_amt = (rates.get('monthly_rate') + flt(header.get('hdmf_inc'), 8)) - flt(header.get('hdmf_ded'), 8)

			if emp.get('payroll_schedule') == "Semi-Monthly" and self.schedule == emp['payroll_schedule']:
				if self.frequency == emp.get('hdmf_freq') or emp.get('hdmf_freq') in ['Both', 'All']:
					target_amt = header.get('prev_govt_basic') + header.get('govt_basic') + \
						(header.get('prev_hdmf_inc') + header.get('hdmf_inc')) - (header.get('prev_hdmf_ded') + header.get('hdmf_ded'))

					if header.get("govt_use_old"):
						target_amt = (rates.get('monthly_rate') + flt(header.get('hdmf_inc'), 8)) - flt(header.get('hdmf_ded'), 8) 

					if emp.get('hdmf_freq') == '1st' and emp.get("rate_type") != "Daily Rate":
						target_amt = rates.get('monthly_rate') + header.get('hdmf_inc') - header.get('hdmf_ded')

					if emp.get('hdmf_freq') == '2nd' and emp.get("rate_type") != "Daily Rate":
						if header.get('prev_monthly_rate') != rates.get('monthly_rate') and header.get('prev_monthly_basis') > 0:
							target_amt = (rates.get('monthly_rate') / 2)+ \
								(header.get('prev_hdmf_inc') + header.get('hdmf_inc')) - (header.get('prev_hdmf_ded') + header.get('hdmf_ded'))

						if header.get("govt_use_old"):
							target_amt = (rates.get('monthly_rate') + flt(header.get('prev_hdmf_inc'), 8)) - flt(header.get('prev_hdmf_ded'), 8)

					if emp.get("rate_type") == "Daily Rate" and header.get('mo_amt_smdl') and header.get('hdmf_smdl'):
						target_amt = rates.get('monthly_rate') + (header.get('prev_hdmf_inc') + header.get('hdmf_inc')) - (header.get('prev_hdmf_ded') + header.get('hdmf_ded'))
						if self.frequency == '1st' and emp.get('hdmf_freq') in ['Both', 'All']:
							target_amt = (rates.get('monthly_rate')/2) + header.get('hdmf_inc') - header.get('hdmf_ded')

			if emp.get('payroll_schedule') == "Weekly" and self.schedule == emp['payroll_schedule']:
				if emp.get('hdmf_mode') == "ME Table":
					if emp.get('hdmf_freq') == "1st" and self.frequency == "2nd":
						target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

					if emp.get('hdmf_freq') == "2nd" and self.frequency in ["4th", "5th"]:
						if cint(header.get("no_weeks")) == cint(5):
							if self.frequency in ["2nd", "5th"]:
								target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

						if cint(header.get("no_weeks")) == cint(4):
							if self.frequency in ["2nd", "4th"]:
								target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

					if emp.get('hdmf_freq') == 'Both':
						if cint(header.get("no_weeks")) == cint(5):
							if self.frequency in ["2nd", "5th"]:
								target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

						if cint(header.get("no_weeks")) == cint(4):
							if self.frequency in ["2nd", "4th"]:
								target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12

					if emp.get('hdmf_freq') == 'All':
						freq_all_passed = 0
						if cint(header.get("no_weeks")) == cint(1):
							if self.frequency in ['1st']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(2):
							if self.frequency in ['1st', '2nd']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(3):
							if self.frequency in ['1st', '2nd', '3rd']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(4):
							if self.frequency in ['1st', '2nd', '3rd', '4th']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(5):
							if self.frequency in ['1st', '2nd', '3rd', '4th', '5th']:
								freq_all_passed = 1

						if freq_all_passed:
							target_amt = (rates.get('daily_rate') * emp.get('total_yr_days')) / 12
				else:
					govt_basis = header.get('govt_basic')
					govt_basis += (header['hdmf_inc'] - header['hdmf_ded'])
					target_amt, monthly_basis = get_weekly_basis('hdmf', emp, header, emp.get('hdmf_freq'), self.frequency, weekly_prev_map, flt(govt_basis, 8) )

			if emp.get('payroll_schedule') == "Weekly" and emp.get('hdmf_mode') in ["ME Table Manual"]:
				if emp.get('hdmf_freq') == "1st" and self.frequency == "2nd":
					target_amt = flt(emp.get("hdmf_manual"), 8)

				if emp.get('hdmf_freq') == "2nd" and self.frequency in ["4th", "5th"]:
					if cint(header.get("no_weeks")) == cint(5):
						if self.frequency in ["2nd", "5th"]:
							target_amt = flt(emp.get("hdmf_manual"), 8)

					if cint(header.get("no_weeks")) == cint(4):
						if self.frequency in ["2nd", "4th"]:
							target_amt = flt(emp.get("hdmf_manual"), 8)

				if emp.get('hdmf_freq') == 'Both':
					if self.frequency == "2nd":
						target_amt = flt(emp.get("hdmf_manual"), 8)

					if cint(header.get("no_weeks")) in [cint(4), cint(5)]:
						if self.frequency in ["2nd", str(cint(header.get("no_weeks")))+"th"]:
							target_amt = flt(emp.get("hdmf_manual"), 8)

				if emp.get('hdmf_freq') == 'All':
					freq_all_passed = 0
					if cint(header.get("no_weeks")) == cint(1):
						if self.frequency in ['1st']:
							freq_all_passed = 1
					if cint(header.get("no_weeks")) == cint(2):
						if self.frequency in ['1st', '2nd']:
							freq_all_passed = 1
					if cint(header.get("no_weeks")) == cint(3):
						if self.frequency in ['1st', '2nd', '3rd']:
							freq_all_passed = 1
					if cint(header.get("no_weeks")) == cint(4):
						if self.frequency in ['1st', '2nd', '3rd', '4th']:
							freq_all_passed = 1
					if cint(header.get("no_weeks")) == cint(5):
						if self.frequency in ['1st', '2nd', '3rd', '4th', '5th']:
							freq_all_passed = 1

					if freq_all_passed:
						target_amt = flt(emp.get("hdmf_manual"), 8)

			if emp.get('hdmf_mode') == "Table Percentage":
				target_amt = header.get('govt_basic') + header.get('hdmf_inc') - header.get('hdmf_ded')

				if emp.get('payroll_schedule') not in ["Weekly"] and self.frequency == '1st' and emp.get('hdmf_freq') == '1st':
					if emp.get('rate_type') not in ["Daily Rate"]:
						target_amt = rates.get('monthly_rate') + header.get('hdmf_inc') - header.get('hdmf_ded')

				if emp.get('payroll_schedule') == "Weekly":
					target_amt = 0
					if emp.get('hdmf_freq') == '1st':
						if self.frequency == '2nd':
							target_amt = rates.get('monthly_rate') + header.get('hdmf_inc') - header.get('hdmf_ded')
							target_prvhdmf = ['1st']

							prv_hdmf = filter(lambda dct: dct['frequency'] in target_prvhdmf, weekly_prev_map[emp['name']]['previous_data'])
							if prv_hdmf:
								for prv in prv_hdmf:
									target_amt += prv['hdmf_inc']
									target_amt -= prv['hdmf_ded']

					if emp.get('hdmf_freq') == '2nd':
						target_prvhdmf = []
						if cint(header.get("no_weeks")) == cint(4) and self.frequency == '4th':
							target_amt = header.get('govt_basic') + header.get('hdmf_inc') - header.get('hdmf_ded')
							target_prvhdmf = ['1st', '2nd', '3rd']

						if cint(header.get("no_weeks")) == cint(5) and self.frequency == '5th':
							target_amt = header.get('govt_basic') + header.get('hdmf_inc') - header.get('hdmf_ded')
							target_prvhdmf = ['1st', '2nd', '3rd', '4th']

						prv_hdmf = filter(lambda dct: dct['frequency'] in target_prvhdmf, weekly_prev_map[emp['name']]['previous_data'])
						if prv_hdmf:
							for prv in prv_hdmf:
								target_amt += prv['government_basis']
								target_amt += prv['hdmf_inc']
								target_amt -= prv['hdmf_ded']

					if emp.get('hdmf_freq') == 'Both':
						target_prvhdmf = []
						if self.frequency == '2nd':
							target_amt = header.get('govt_basic') + header.get('hdmf_inc') - header.get('hdmf_ded')
							target_prvhdmf = ['1st']

						if cint(header.get("no_weeks")) == cint(4) and self.frequency == '4th':
							target_amt = header.get('govt_basic') + header.get('hdmf_inc') - header.get('hdmf_ded')
							target_prvhdmf = ['1st', '2nd', '3rd']

						if cint(header.get("no_weeks")) == cint(5) and self.frequency == '5th':
							target_amt = header.get('govt_basic') + header.get('hdmf_inc') - header.get('hdmf_ded')
							target_prvhdmf = ['1st', '2nd', '3rd', '4th']

						if target_prvhdmf:
							prv_hdmf = filter(lambda dct: dct['frequency'] in target_prvhdmf, weekly_prev_map[emp['name']]['previous_data'])
							if prv_hdmf:
								for prv in prv_hdmf:
									target_amt += prv['government_basis']
									target_amt += prv['hdmf_inc']
									target_amt -= prv['hdmf_ded']

					if emp.get('hdmf_freq') == 'All':
						target_amt = header.get('govt_basic') + header.get('hdmf_inc') - header.get('hdmf_ded')
						target_prvhdmf = []
						if self.frequency == '2nd':
							target_prvhdmf = ['1st']

						if self.frequency == '3rd':
							target_prvhdmf = ['1st', '2nd']

						if cint(header.get("no_weeks")) == cint(4) and self.frequency == '4th':
							target_prvhdmf = ['1st', '2nd', '3rd']

						if cint(header.get("no_weeks")) == cint(5):
							if self.frequency == '4th':
								target_prvhdmf = ['1st', '2nd', '3rd']
							if self.frequency == '5th':
								target_prvhdmf = ['1st', '2nd', '3rd', '4th']

						prv_hdmf = filter(lambda dct: dct['frequency'] in target_prvhdmf, weekly_prev_map[emp['name']]['previous_data'])
						if prv_hdmf:
							for prv in prv_hdmf:
								target_amt += prv['government_basis']
								target_amt += prv['hdmf_inc']
								target_amt -= prv['hdmf_ded']

					if cint(header.get("no_weeks")) == cint(4) and self.frequency == '5th':
						target_amt = 0

				if emp.get('payroll_schedule') == "Semi-Monthly" and emp.get('hdmf_freq') == '2nd' and self.frequency == '2nd':
					target_amt = header.get('prev_govt_basic') + header.get('govt_basic') + \
						(header.get('prev_hdmf_inc') + header.get('hdmf_inc')) - (header.get('prev_hdmf_ded') + header.get('hdmf_ded'))

				if emp.get('payroll_schedule') == "Semi-Monthly" and emp.get('hdmf_freq') == 'Both' and self.frequency == '2nd':
					target_amt = header.get('prev_govt_basic') + header.get('govt_basic') + \
						(header.get('prev_hdmf_inc') + header.get('hdmf_inc')) - (header.get('prev_hdmf_ded') + header.get('hdmf_ded'))

				if emp.get('payroll_schedule') == "Semi-Monthly" and emp.get("rate_type") == "Daily Rate" and header.get('mo_amt_smdl') and header.get('hdmf_smdl'):
					yrdays = flt(emp.get('total_yr_days'), 8)/12
					target_amt = ((rates.get('daily_rate') * yrdays) / 2) + (header.get('hdmf_inc') - header.get('hdmf_ded'))

					if self.frequency == '2nd':
						target_amt = ((rates.get('daily_rate') * yrdays)) + (header.get('hdmf_inc') + header.get('prev_hdmf_inc')) - (header.get('hdmf_ded') + header.get('prev_hdmf_ded'))

				if emp.get('payroll_schedule') == "Monthly" and emp.get("rate_type") == "Daily Rate" and header.get('mo_amt_smdl') and header.get('hdmf_smdl'):
					target_amt = rates.get('monthly_rate') + (header.get('hdmf_inc') - header.get('hdmf_ded'))

				if emp.get('payroll_schedule') == "Semi-Monthly" and emp.get('hdmf_freq') == '2nd' and self.frequency == '1st':
					target_amt = 0

				if emp.get('payroll_schedule') == "Semi-Monthly" and emp.get('hdmf_freq') == '1st' and self.frequency == '2nd':
					target_amt = 0

			if target_amt and emp.get('hdmf_mode') != "None":
				hdmf, hdmfe = get_hdmf_amount(target_amt, hdmf_table)

				#HDMF Manual Triggers
				if emp.get('payroll_schedule') == "Weekly" and emp.get('hdmf_mode') == "ME Table Manual":
					if emp.get('hdmf_freq') == "1st" and self.frequency == "2nd":
						hdmfm = flt(emp.get("hdmf_manual"), 8)

					if emp.get('hdmf_freq') == "2nd" and self.frequency in ["4th", "5th"]:
						if cint(header.get("no_weeks")) == cint(5):
							if self.frequency in ["2nd", "5th"]:
								hdmfm = flt(emp.get("hdmf_manual"), 8)

						if cint(header.get("no_weeks")) == cint(4):
							if self.frequency in ["2nd", "4th"]:
								hdmfm = flt(emp.get("hdmf_manual"), 8)

					if emp.get('hdmf_freq') == 'Both':
						if self.frequency == "2nd":
							hdmfm = flt(emp.get("hdmf_manual"), 8)

						if cint(header.get("no_weeks")) in [cint(4), cint(5)]:
							if self.frequency in ["2nd", str(cint(header.get("no_weeks")))+"th"]:
								hdmfm = flt(emp.get("hdmf_manual"), 8)

					if emp.get('hdmf_freq') == 'All':
						freq_all_passed = 0
						if cint(header.get("no_weeks")) == cint(1):
							if self.frequency in ['1st']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(2):
							if self.frequency in ['1st', '2nd']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(3):
							if self.frequency in ['1st', '2nd', '3rd']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(4):
							if self.frequency in ['1st', '2nd', '3rd', '4th']:
								freq_all_passed = 1
						if cint(header.get("no_weeks")) == cint(5):
							if self.frequency in ['1st', '2nd', '3rd', '4th', '5th']:
								freq_all_passed = 1

						if freq_all_passed:
							hdmfm = flt(emp.get("hdmf_manual"), 8)

					if hdmfm > 100:
						hdmf = 100
						hdmfe = 100
						hdmfm = hdmfm - 100
					else:
						hdmf = hdmfm
						hdmfe = hdmfm
						hdmfm = hdmfm 

				if emp.get('hdmf_mode') == "Manual" and emp.get('hdmf_manual'):
					hdmfm = emp.get('hdmf_manual')
					if hdmfm > 100:
						hdmf = 100
						hdmfe = 100
						hdmfm = hdmfm - 100
					else:
						hdmf = hdmfm
						hdmfe = hdmfm
						hdmfm = hdmfm

					if emp.get('payroll_schedule') == "Semi-Monthly" and emp.get('hdmf_freq') in ["Both", "All"]:
						hdmf = hdmf / 2
						hdmfe = hdmfe / 2
						hdmfm = hdmfm / 2

				elif header.get('hdmf_strm') == 1 and emp.get('hdmf_mode') == "Manual":
					if self.frequency == emp.get('hdmf_freq') or emp.get('hdmf_freq') == 'Both':
						hdmf_register = []
						hdmf_list = ["hdmf","hdmfe","hdmfm"]
						hdmf, hdmfe, hdmfm = 0, 0, 0
						target_amt = 0

						if emp.get('payroll_schedule') == "Semi-Monthly" and emp.get('hdmf_freq') == 'Both':
							hdmf = flt(emp.get('hdmf_manual'), 8) / 2
							hdmfe = 50
						elif emp.get('payroll_schedule') == "Monthly":
							hdmf = emp.get('hdmf_manual')
							hdmfe = 100

				if emp.get('hdmf_mode') == "Table Percentage":
					hdmf_tablepercentage = frappe.db.sql("""SELECT `minimum`, `maximum`, `employee_rate`, `employer_rate` FROM `tabHDMF Table Percentage` """, as_dict=1 )
					hdmf, hdmfe = 0, 0

					for tp in hdmf_tablepercentage:
						if tp.minimum <= target_amt <= tp.maximum:
							hdmf = flt(target_amt) * ((flt(tp.employee_rate, 8) / 100))
							hdmfe = flt(target_amt) * ((flt(tp.employer_rate, 8) / 100))

						if target_amt >= 5000:
							hdmf = 100
							hdmfe = 100

				#set to zero if HDMFM is negative
				if hdmfm < 1:
					hdmfm = 0

				for l in hdmf_list:
					amt = flt(eval(l), 8)

					if emp.get('payroll_schedule') == "Semi-Monthly" and emp.get('hdmf_freq') == "Both":
						if emp.get('hdmf_mode') != "Manual":
							amt = abs(flt(eval(l), 8) / 2)

					if emp.get('payroll_schedule') == "Weekly" and emp.get('hdmf_freq') == "Both":
						if emp.get('hdmf_mode') == "ME Table":
							if self.frequency == '2nd':
								amt = abs(flt(eval(l), 8) / 2)

							if self.frequency != '2nd':
								if weekly_prev_map and emp['name'] in weekly_prev_map:
									prv_hdmf = filter(lambda dct: dct['frequency'] in ['2nd'], weekly_prev_map[emp['name']]['previous_data'])
									if prv_hdmf:
										amt = abs(flt(eval(l), 8) - prv_hdmf[0][l])

						if emp.get('hdmf_mode') == "ME Table Manual":
							amt = abs(flt(eval(l), 8) / 2)

						if emp.get('hdmf_mode') == "Table":
							amt = abs(flt(eval(l), 8) / 2)

					if emp.get('payroll_schedule') == "Weekly" and emp.get('hdmf_freq') == "All":
						if emp.get('hdmf_mode') == "ME Table":
							amt = flt(eval(l), 8) / cint(header.get("no_weeks"))
						if emp.get('hdmf_mode') == "Table":
							amt = flt(eval(l), 8) / cint(header.get("no_weeks"))
						if emp.get('hdmf_mode') == "ME Table Manual":
							amt = flt(eval(l), 8) / cint(header.get("no_weeks"))
	#					if emp.get('hdmf_mode') == "Table" and l == 'hdmfm':
	#						amt = 0
	#						if cint(header.get("no_weeks")) == 4 and self.frequency == '4th':
	#							amt = flt(eval(l), 8)
	#						if cint(header.get("no_weeks")) == 5 and self.frequency == '5th':
	#							amt = flt(eval(l), 8)

					if emp.get('hdmf_mode') not in ["Manual", "ME Table Manual"]:
						#For EE
						if emp.get('hdmf_freq') in ["Both" "All"]:
							if header.get('prev_hdmf_amt'):
								if l.upper() == 'HDMF':
									amt = amt - header.get('prev_hdmf_amt')
							else:
								if emp.get('payroll_schedule') == "Semi-Monthly":
									amt = flt(eval(l), 8) / 2

							if l.upper() == 'HDMFE':
								if header.get('prev_hdmf_er_amt'):
									amt = amt - header.get('prev_hdmf_er_amt')
								else:
									if emp.get('payroll_schedule') == "Semi-Monthly":
										amt = flt(eval(l), 8) / 2

					if emp.get('hdmf_mode') in ["Table Percentage"]:
						amt = flt(eval(l), 8)

						if l =='hdmf' and (header.get('prev_hdmf_amt') + amt) >= 100:
							amt = abs(amt - header.get('prev_hdmf_amt'))

						if l =='hdmf' and header.get('prev_hdmf_amt') >= 100:
							amt = 0

						if l =='hdmfe' and (header.get('prev_hdmf_er_amt') + amt) >= 100:
							amt = abs(amt - header.get('prev_hdmf_er_amt'))

						if l =='hdmfe' and header.get('prev_hdmf_er_amt') >= 100:
							amt = 0

						if emp.get('payroll_schedule') == "Weekly":
							weekly_hdmf = 0
							weekly_hdmfe = 0
							curfrqstr = str(self.frequency)[:1]
							for prv in weekly_prev_map[emp['name']]['previous_data']:
								frqstr = str(prv['frequency'])[:1]
								if int(frqstr) < int(curfrqstr):
									if l =='hdmf':
										weekly_hdmf += prv['hdmf']
									if l =='hdmfe':
										weekly_hdmfe += prv['hdmfe']

							if emp.get('hdmf_freq') in ['Both', 'All']:
								if l =='hdmf':
									amt = abs(amt - weekly_hdmf)
								if l =='hdmfe':
									amt = abs(amt - weekly_hdmfe)

								if amt > 100:
									amt = 0
							else:
								if l =='hdmf' and (weekly_hdmf + amt ) >= 100:
									amt = abs(amt - weekly_hdmf)
								if l =='hdmfe' and (weekly_hdmfe + amt ) >= 100:
									amt = abs(amt - weekly_hdmfe)
								if l =='hdmf' and weekly_hdmf >= 100:
									amt = 0
								if l =='hdmfe' and weekly_hdmfe >= 100:
									amt = 0

						if amt:
							if emp.get('payroll_schedule') == "Semi-Monthly" and emp.get('hdmf_freq') == 'Both' and self.frequency == '2nd':
								if l =='hdmf':
									amt = abs(flt(eval(l), 8) - header.get('prev_hdmf_amt'))
									if amt > 100:
										amt = 100
								if l =='hdmfe':
									amt = abs(flt(eval(l), 8) - header.get('prev_hdmf_er_amt'))
									if amt > 100:
										amt = 100

					if emp.get('hdmf_mode') in ["Manual"] and emp.get('payroll_schedule') == "Weekly":
						amt = 0

					if amt < 1:
						amt = 0

					hdmf_register.append({"pay_code": l.upper(), "amount": amt })

		if emp.get('hdmf_mode') != "None":
			for d in hdmf_register:
				register.append(d)
				if d.get("pay_code") == "HDMF" and d.get('amount') > 0:
					header['hdmf_amt'] = d.get('amount')

				if d.get("pay_code") == "HDMFM" and d.get('amount') > 0:
					header['hdmf_manual'] = d.get('amount')

				if d.get('pay_code') == "HDMFE" and d.get('amount') > 0:
					header['hdmf_er_amt'] = d.get('amount')

				if d.get("pay_code") == "HDMF" or d.get("pay_code") == "HDMFM":
					self.calculate_special_header(d, header, tr_map)

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

	def get_previous_period(self):
		previous_period = ""
		conditions = ""
		period_group = frappe.db.get_value("Payroll Period", self.period, ["period_group"])
		strict_period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')
		if period_group and strict_period_group:
			conditions = "AND period_group='{0}'".format(period_group)

		if self.schedule != "Weekly" and self.frequency != '1st':
			before = frappe.db.sql_list(""" SELECT `name` FROM `tabPayroll Period` WHERE frequency != "Special" AND company = %(company)s 
				AND `schedule` = %(schedule)s AND payroll_date < %(payroll_date)s {conditions} ORDER BY payroll_date DESC LIMIT 1 """.format(conditions=conditions),({ 
				"company": self.company,
				"schedule": self.schedule,
				"payroll_date": self.payroll_date,
			}))
			
			previous_period = before[0] if before else ""

		return previous_period

	def get_previous(self, emp, header):
		if self.schedule != "Weekly":
			previous = frappe.db.sql(""" SELECT monthly_rate, taxable_income, taxable_deduction, gross_payroll, 
				present_days, work_days, absent_days, govt_basic,
				sss_inc, sss_ded, sss_amt, sss_er_amt, sss_ec_amt, sss_er_mpf, sss_ee_mpf,
				phic_inc, phic_ded, phic_amt, phic_er_amt, phic_ec_amt, 
				hdmf_inc, hdmf_ded, hdmf_amt, hdmf_manual, hdmf_er_amt, hdmf_ec_amt,
				whtax_amt
				FROM `tabPayroll Register` 
				WHERE period = %s AND employee = %s LIMIT 1 """,(header.get('previous_period'), emp.get('name')), as_dict=True)		
			for d in previous:
				header['prev_monthly_rate'] = flt(d.monthly_rate, 8)
				header['prev_govt_basic'] = flt(d.govt_basic, 8)
				header['prev_sss_inc'] = flt(d.sss_inc, 8)
				header['prev_sss_ded'] = flt(d.sss_ded, 8)
				header['prev_sss_amt'] = flt(d.sss_amt, 8)
				header['prev_sss_er_amt'] = flt(d.sss_er_amt, 8)
				header['prev_sss_ec_amt'] = flt(d.sss_ec_amt, 8)
				header['prev_sss_er_mpf'] = flt(d.sss_er_mpf, 8)
				header['prev_sss_ee_mpf'] = flt(d.sss_ee_mpf, 8)		
				header['prev_phic_inc'] = flt(d.phic_inc, 8)
				header['prev_phic_ded'] = flt(d.phic_ded, 8)
				header['prev_phic_amt'] = flt(d.phic_amt, 8)
				header['prev_phic_er_amt'] = flt(d.phic_er_amt, 8)
				header['prev_phic_ec_amt'] = flt(d.phic_ec_amt, 8)
				header['prev_hdmf_inc'] = flt(d.hdmf_inc, 8)
				header['prev_hdmf_ded'] = flt(d.hdmf_ded, 8)
				header['prev_hdmf_amt'] = flt(d.hdmf_amt, 8)
				header['prev_hdmf_er_amt'] = flt(d.hdmf_er_amt, 8)
				header['prev_hdmf_ec_amt'] = flt(d.hdmf_ec_amt, 8)
				header['prev_hdmf_manual'] = flt(d.hdmf_manual, 8)
				header['prev_whtax_amt'] = flt(d.whtax_amt, 8)
				header['previous_taxable_income'] = flt(d.taxable_income, 8)
				header['prev_tax_ded'] = flt(d.taxable_deduction, 8)
				header['previous_gross_payroll'] = flt(d.gross_payroll, 8)
				header['previous_present_days'] = flt(d.present_days, 8)
				header['previous_work_days'] = flt(d.work_days, 8)
				header['previous_absent_days'] = flt(d.absent_days, 8)