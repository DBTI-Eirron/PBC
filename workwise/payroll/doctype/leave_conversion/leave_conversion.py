# -*- coding: utf-8 -*-
# Copyright (c) 2020, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _
from workwise.payroll.payroll_utils import get_transaction_map, get_overtime_map, get_adjustment_settings, get_rates
from workwise.time_keeping.application_utils import validate_inactive_employee

class LeaveConversion(Document):
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

	def validate_leave_type(self):
		if not frappe.db.get_value("Leave Type", self.lv_convert, "convertible"):
			frappe.throw(_("Leave Type is not convertible"))

	def process_special(self):
		self.validate_employee()
		self.validate_period()
		self.validate_leave_type()
		ss_list = 0
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
			"Leave Balance to Cash": self.leave_balance_to_cash,
			"Leave Filing Convert to Cash": self.leave_to_cash,
		}

		func = switcher.get(self.method, lambda: frapp.throw(_("Invalid Method")))
		func(header, entries)

		if entries:
			ss_list = 1
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

	def leave_balance_to_cash(self, header, entries):
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
				lb_entries = frappe.db.sql(""" SELECT * FROM `tabLB Entry` WHERE `employee` = %s AND (`leave_type` = %s OR `deduct_credits_to` = %s) ORDER BY `from_date` ASC """, (emp.name, self.lv_convert, self.lv_convert), as_dict=1)
				for d in lb_entries:
					if d.balance_type == "Add":
						if self.lv_convert == d.leave_type:
							if d.name not in valid_entry:
								valid_entry[d.name] = {
									"credits": d.credits,
									"from": getdate(d.from_date),
									"to": getdate(d.to_date),
								}
					else:
						if d.deduct_credits_to == self.lv_convert:
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
					if (( valid_entry[vl]['from'] <= getdate(from_year) <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= getdate(to_year) <= valid_entry[vl]['to'] ))\
					or (( getdate(from_year) <= valid_entry[vl]['from'] <= getdate(to_year) ) or ( getdate(from_year) <= valid_entry[vl]['to'] <= getdate(to_year) )):
						total_balance += valid_entry[vl]['credits']
				
				if total_balance <= 0:
					total_balance = 0

				total_amt = total_balance * rates.get('daily_rate')

				if total_amt > 0:
					entries.append({
						"employee": emp.name,
						"employee_name": emp.full_name, 
						"amount": total_amt,
					})

		return header, entries

	def leave_to_cash(self, header, entries):
		attendance_from, attendance_to = frappe.db.get_value("Payroll Period", self.period, ["attendance_from","attendance_to"])
		header['transaction_type'] = self.convert_to
		header['remarks'] = ("Leave Converted to cash from {0} to {1}").format(attendance_from, attendance_to)
		
		employees = self.get_employees()
		if employees:
			emp_map = frappe._dict()
			for emp in employees:
				emp_map.setdefault(emp.name, frappe._dict({
						"employee": emp.name,
						"employee_name": emp.full_name,
						"employee_details": emp,
						"leaves": [],
						"amount": 0.0,
					})
				)

			#Get Leaves
			leaves = frappe.db.sql("""SELECT LA.`name`, LA.employee, LA.full_name, LAT.leave_date, LA.leave_type, LAT.is_half_day, LAT.is_excluded, LA.remarks 
				FROM `tabLeave Application` LA 
				INNER JOIN `tabLeave Application Table` LAT ON LAT.parent = LA.`name`
				WHERE company = %(company)s 
				AND LAT.leave_date >= %(from_date)s 
				AND LAT.leave_date <= %(to_date)s
				AND LA.leave_type = %(leave_type)s
				AND LA.convert_cash = 1 AND LA.docstatus = 1 AND LAT.is_excluded != 1 """,{ 
					"company": self.company,
					"leave_type": self.lv_convert,
					"from_date": attendance_from,
					"to_date": attendance_to,
				}, as_dict=True)

			#Insert to dict Leaves per Employee
			for ll in leaves:
				if ll.employee in emp_map:
					emp_map[ll.employee].leaves.append(ll)

			#Total Leaves per employee
			for e, edict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
				rates = get_rates(emp)
				for lv in edict['leaves']:
					if lv.is_half_day:
						edict['amount'] += (flt(0.5, 8) * flt(rates.get('daily_rate'), 8))
					else:
						edict['amount'] += flt(rates.get('daily_rate'), 8)

				if edict['amount'] > 0:
					entries.append({
						"employee": edict['employee'],
						"employee_name": edict['employee_name'], 
						"amount": edict['amount'],
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
		log = "<p>" + _("No Special Entries created") + "</p>"
		if ss_list:
			log = "<p>" + _("Special Entries created") + "</p>"

		return log