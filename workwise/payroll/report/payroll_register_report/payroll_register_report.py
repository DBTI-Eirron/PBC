# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	validate_filters(filters)

	employee_list = get_employees(filters)
	columns, income_types, deduction_types = get_columns(filters,employee_list)

	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list
	else:
		income_map = get_income_map(filters, employee_list)
		deduction_map = get_deduction_map(filters, employee_list)

		data = []
		dtotal_income, dtotal_deduction, dtotal_payroll = 0.00, 0.00, 0.00
		income_total, deduction_total = [], []
		total_present = 0

		for income in income_types:
			income_total.append(0)

		for deduction in deduction_types:
			deduction_total.append(0)

		for emp in employee_list:
			row = [emp.employee, emp.employee_name, emp.present_days]
			total_present += emp.present_days
			total_income = 0.00
			i = 0
			for income in income_types:
				income_amount = flt(income_map.get(emp.employee, {}).get(income), 8)
				total_income += flt(income_amount, 8)
				income_total[i] += flt(income_amount, 8)
				row.append('{:,.2f}'.format(income_amount))
				i += 1

			total_deduction = 0.00
			i = 0
			for deduction in deduction_types:
				deduction_amount = flt(deduction_map.get(emp.employee, {}).get(deduction), 8)
				total_deduction += flt(deduction_amount, 8)
				deduction_total[i] += flt(deduction_amount, 8)
				row.append('{:,.2f}'.format(deduction_amount))
				i += 1

			total_payroll = flt(total_income, 8) - flt(total_deduction, 8)
			if total_payroll < 0:
				total_payroll = 0.00
			row += ['{:,.2f}'.format(total_income), '{:,.2f}'.format(total_deduction), '{:,.2f}'.format(total_payroll)]
			dtotal_income += total_income
			dtotal_deduction += total_deduction
			dtotal_payroll += total_payroll
			data.append(row)
		total_row = ["<b> Total</b>","",total_present]
		if filters.hide_zero:
			i = 0
			for income in income_types:
				if income_total[i] > 0:
					total_row.append('{:,.2f}'.format(income_total[i]))
					i += 1
				else:
					del columns[i+3]
					del income_total[i]
					for d in data:
						del d[i+3]
						
			inlen = i
			i = 0
			for deduction in deduction_types:
				if deduction_total[i] > 0:
					total_row.append('{:,.2f}'.format(deduction_total[i]))
					i += 1
				else:
					del columns[i+inlen+3]
					del deduction_total[i]
					for d in data:
						del d[i+inlen+3]
		else:
			i = 0
			for income in income_types:
				total_row.append('{:,.2f}'.format(income_total[i]))
				i += 1

			i = 0
			for deduction in deduction_types:
				total_row.append('{:,.2f}'.format(deduction_total[i]))
				i += 1

		total_row += ['{:,.2f}'.format(dtotal_income), '{:,.2f}'.format(dtotal_deduction), '{:,.2f}'.format(dtotal_payroll)]
		data.append(total_row)

	return columns, data

def validate_filters(filters):
	if filters.payroll_period:
		period_company = frappe.db.get_value("Payroll Period", filters.payroll_period, 'company')
		if period_company != filters.company:
			frappe.throw(_("Period {0} Does not belong to company {1}").format(filters.payroll_period, filters.company))

	if filters.employee:
		emp_company = frappe.db.get_value("Employee", filters.employee, 'company')
		if emp_company != filters.company:
			frappe.throw(_("Employee {0} Does not belong to company {1}").format(filters.employee, filters.company))

def get_columns(filters,employee_list):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "present_days",
			"label": _("Present Days"),
			"fieldtype": "Data",
			"width": 120
		},
	]
	
	income_types = frappe.db.sql_list(""" SELECT code
		FROM `tabTransaction Type` WHERE `type` = 'Income' ORDER BY sort """)

	deduction_types = frappe.db.sql_list(""" SELECT code
		FROM `tabTransaction Type` WHERE `type` = 'Deduction' ORDER BY sort""")

	if employee_list:
		for pay_code in income_types:	
			pay_title = frappe.db.get_value("Transaction Type", pay_code, 'title')
			columns.append({			
				"fieldname": pay_code,
				"label": pay_title,
				"fieldtype": "Float",
				"width": 100
			})

		for pay_code in deduction_types:
			pay_title = frappe.db.get_value("Transaction Type", pay_code, 'title')
			columns.append({			
				"fieldname": pay_code,
				"label": pay_title,
				"fieldtype": "Float",
				"width": 100
			})

	columns += [
		{
			"fieldname": "total_income",
			"label": _("Total Income"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "total_deduction",
			"label": _("Total Deduction"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "total_payroll",
			"label": _("Total Payroll"),
			"fieldtype": "Float",
			"width": 100
		},
	]

	return columns, income_types, deduction_types

def get_employees(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql("""SELECT DISTINCT PR.employee, PR.employee_name, PR.present_days
		FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		WHERE TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s)
			AND PR.on_hold = 0
			AND PR.period = %(period)s
			AND PR.company = %(company)s {conditions} ORDER BY PR.employee_name""".format(conditions=get_conditions(filters)), { 
				"period": filters.payroll_period,
				"company": filters.company,
				"user": cur_user,
				"employee": filters.employee,
				"location": filters.location,
			}, as_dict=1)
	else:
		employees = frappe.db.sql("""SELECT DISTINCT PR.employee, PR.employee_name, PR.present_days
		FROM `tabPayroll Register` PR JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		WHERE PR.period = %(period)s
			AND PR.on_hold = 0
			AND TE.company = %(company)s {conditions} ORDER BY PR.employee_name""".format(conditions=get_conditions(filters)), { 
				"period": filters.payroll_period,
				"company": filters.company,
				"employee": filters.employee,
				"location": filters.location
			}, as_dict=1)

	return employees

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("PR.employee=%(employee)s")

	if filters.get("location"):
		conditions.append("TE.`location`=%(location)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 

def get_income_map(filters, employee_list):
	income_details = frappe.db.sql("""SELECT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		WHERE PR.period = %s AND employee in (%s) GROUP BY PRE.`name` """ %
		('%s',', '.join(['%s']*len(employee_list))), tuple([filters.payroll_period] + [emp.employee for emp in employee_list]), as_dict=1)

	income_map = {}
	for d in income_details:
		income_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
		if income_map[d.employee][d.pay_code]:
			income_map[d.employee][d.pay_code] += flt(d.amount, 8)
		else:
			income_map[d.employee][d.pay_code] = flt(d.amount, 8)

	return income_map

def get_deduction_map(filters, employee_list):
	deduction_details = frappe.db.sql("""SELECT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		WHERE PR.period = %s AND employee in (%s) GROUP BY PRE.`name` """ %
		('%s',', '.join(['%s']*len(employee_list))), tuple([filters.payroll_period] + [emp.employee for emp in employee_list]), as_dict=1)

	deduction_map = {}
	for d in deduction_details:
		deduction_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
		if deduction_map[d.employee][d.pay_code]:
			deduction_map[d.employee][d.pay_code] += flt(d.amount, 8)
		else: 
			deduction_map[d.employee][d.pay_code] = flt(d.amount, 8)

	return  deduction_map