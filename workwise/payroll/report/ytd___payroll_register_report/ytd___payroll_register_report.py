# Copyright (c) 2013, OSI and contributors

# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import get_rates, format_precision, format_align_right
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	validate_filters(filters)

	from_date = datetime.date(int(filters.payroll_year),1,1)
	to_date = datetime.date(int(filters.payroll_year),12,31)
	employee_list = get_employees(filters,from_date,to_date)

	columns, income_types, deduction_types = get_columns(filters,employee_list)
	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list
	else:
		income_map = get_income_map(filters, employee_list, from_date, to_date)
		deduction_map = get_deduction_map(filters, employee_list, from_date, to_date)

		data = []
		dtotal_income, dtotal_deduction, dtotal_payroll = 0.00, 0.00, 0.00
		income_total, deduction_total = [], []
		total_present = 0

		for income in income_types:
			income_total.append(0)

		for deduction in deduction_types:
			deduction_total.append(0)

		for emp in employee_list:
			# rates = get_rates(emp)
			# period_type = frappe.get_value('Payroll Period', filters.payroll_period, 'schedule')
			# if period_type == 'Weekly':
			# 	rate = flt(rates['weekly_rate'])
			# elif period_type == 'Semi-Monthly':
			# 	rate = flt(rates['semi_rate'])
			# elif period_type == 'Monthly':
			# 	rate = flt(rates['monthly_rate'])
			# final_rate = emp.min_take_home if emp.mth_percentage == 0 else rate * (emp.min_take_home/100)
			# if final_rate <= emp.net_payroll:
			row = [emp, employee_list[emp]['employee_name'], employee_list[emp]['present_days']]
			total_present += employee_list[emp]['present_days']
			total_income = 0.00
			i = 0
			for income in income_types:
				income_amount = flt(income_map.get(emp, {}).get(income), 8)
				total_income += flt(income_amount, 8)
				income_total[i] += flt(income_amount, 8)
				row.append(format_precision(income_amount, filters.value_precision))
				i += 1

			total_deduction = 0.00
			i = 0
			for deduction in deduction_types:
				deduction_amount = flt(deduction_map.get(emp, {}).get(deduction), 8)
				total_deduction += flt(deduction_amount, 8)
				deduction_total[i] += flt(deduction_amount, 8)
				row.append(format_precision(deduction_amount, filters.value_precision))
				i += 1

			total_payroll = flt(total_income, 8) - flt(total_deduction, 8)
			if total_payroll < 0:
				total_payroll = 0.00
			row += [format_precision(total_income, filters.value_precision), format_precision(total_deduction, filters.value_precision), format_precision(total_payroll, filters.value_precision)]
			dtotal_income += total_income
			dtotal_deduction += total_deduction
			dtotal_payroll += total_payroll
			data.append(row)
		total_row = ["<b> Total</b>","",total_present]
		if filters.hide_zero:
			i = 0
			for income in income_types:
				if income_total[i] > 0:
					total_row.append(format_precision(income_total[i], filters.value_precision))
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
					total_row.append(format_precision(deduction_total[i], filters.value_precision))
					i += 1
				else:
					del columns[i+inlen+3]
					del deduction_total[i]
					for d in data:
						del d[i+inlen+3]
		else:
			i = 0
			for income in income_types:
				total_row.append(format_precision(income_total[i], filters.value_precision))
				i += 1

			i = 0
			for deduction in deduction_types:
				total_row.append(format_precision(deduction_total[i], filters.value_precision))
				i += 1

		total_row += [format_precision(dtotal_income, filters.value_precision), format_precision(dtotal_deduction, filters.value_precision), format_precision(dtotal_payroll, filters.value_precision)]
		data.append(total_row)

	return columns, data

def validate_filters(filters):
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
				"fieldtype": "Data",
				"width": 100
			})

		for pay_code in deduction_types:
			pay_title = frappe.db.get_value("Transaction Type", pay_code, 'title')
			columns.append({			
				"fieldname": pay_code,
				"label": pay_title,
				"fieldtype": "Data",
				"width": 100
			})

	columns += [
		{
			"fieldname": "total_income",
			"label": _("Total Income"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "total_deduction",
			"label": _("Total Deduction"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "total_payroll",
			"label": _("Total Payroll"),
			"fieldtype": "Data",
			"width": 100
		},
	]

	return columns, income_types, deduction_types

def get_employees(filters,from_date,to_date):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql("""SELECT PR.employee, PR.employee_name, PR.present_days
		FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		WHERE TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s)
			AND PR.on_hold = 0
			AND PR.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND PR.company = %(company)s {conditions} ORDER BY PR.employee_name""".format(conditions=get_conditions(filters)), { 
				"from_date": from_date,
				"to_date": to_date,
				"company": filters.company,
				"user": cur_user,
				"employee": filters.employee,
				"location": filters.location,
			}, as_dict=1)
	else:
		employees = frappe.db.sql("""SELECT PR.employee, PR.employee_name, PR.present_days
		FROM `tabPayroll Register` PR JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		WHERE PR.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND PR.on_hold = 0
			AND TE.company = %(company)s {conditions} ORDER BY PR.employee_name""".format(conditions=get_conditions(filters)), { 
				"from_date": from_date,
				"to_date": to_date,
				"company": filters.company,
				"employee": filters.employee,
				"location": filters.location
			}, as_dict=1)

	employee_map = {}
	for emp in employees:
		if emp.employee not in employee_map:
			employee_map.setdefault(emp.employee, frappe._dict({'employee_name':emp.employee_name, 'present_days':0.0}))
		employee_map[emp.employee]['present_days'] += emp.present_days
	return employee_map

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("PR.employee=%(employee)s")

	if filters.get("location"):
		conditions.append("TE.`location`=%(location)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 

def get_income_map(filters, employee_list, from_date, to_date):
	income_details = frappe.db.sql("""SELECT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		WHERE PR.posting_date BETWEEN %s and %s AND employee in (%s) GROUP BY PRE.`name` """ %
		('%s','%s',', '.join(['%s']*len(employee_list))), tuple([from_date]+ [to_date]  + [emp for emp in employee_list]), as_dict=1)

	income_map = {}
	for d in income_details:
		income_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
		if income_map[d.employee][d.pay_code]:
			income_map[d.employee][d.pay_code] += flt(d.amount, 8)
		else:
			income_map[d.employee][d.pay_code] = flt(d.amount, 8)

	return income_map

def get_deduction_map(filters, employee_list, from_date, to_date):
	deduction_details = frappe.db.sql("""SELECT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		WHERE PR.posting_date BETWEEN %s and %s AND employee in (%s) GROUP BY PRE.`name` """ %
		('%s','%s',', '.join(['%s']*len(employee_list))), tuple([from_date]+ [to_date] + [emp for emp in employee_list]), as_dict=1)

	deduction_map = {}
	for d in deduction_details:
		deduction_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
		if deduction_map[d.employee][d.pay_code]:
			deduction_map[d.employee][d.pay_code] += flt(d.amount, 8)
		else: 
			deduction_map[d.employee][d.pay_code] = flt(d.amount, 8)

	return  deduction_map
