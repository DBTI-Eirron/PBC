
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
		totals={}
		if filters.include_header:
			data.append(["<b>"+filters.company+"</b>"])
			data.append(["<b>"+filters.payroll_period+"</b>"])
			if filters.location:
				data.append(["<b>"+filters.location+"</b>"])
			data.append({})
			header = []
			for col in columns:
				header.append(col['fieldlabel'])
			data.append(header)

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
			if emp.mth_percentage == 0:
				final_rate = emp.min_take_home 
			else:
				final_rate = (emp.total_income * (emp.min_take_home/100))

			if final_rate < emp.net_payroll and emp.net_payroll > 0:
				row = [emp.employee, emp.employee_name, emp.present_days]
				if filters.employee_details:
					row.append(emp.position_title)
				total_present += emp.present_days
				total_income = 0.00
				i = 0
				for income in income_types:
					income_amount = flt(income_map.get(emp.employee, {}).get(income), 8)
					total_income += flt(income_amount, 8)
					income_total[i] += flt(income_amount, 8)
					row.append(format_precision(income_amount, filters.value_precision))
					if income not in totals:
						totals[income] = 0
					totals[income] += flt(income_amount, 8)

					i += 1

				total_deduction = 0.00
				i = 0
				for deduction in deduction_types:
					deduction_amount = flt(deduction_map.get(emp.employee, {}).get(deduction), 8)
					total_deduction += flt(deduction_amount, 8)
					deduction_total[i] += flt(deduction_amount, 8)
					row.append(format_precision(deduction_amount, filters.value_precision))
					if deduction not in totals:
						totals[deduction] = 0
					totals[deduction] += flt(deduction_amount, 8)
					i += 1

				total_payroll = flt(total_income, 8) - flt(total_deduction, 8)
				if total_payroll < 0:
					total_payroll = 0.00
				row += [format_precision(total_income, filters.value_precision), format_precision(total_deduction, filters.value_precision), format_precision(total_payroll, filters.value_precision)]
				dtotal_income += total_income
				dtotal_deduction += total_deduction
				dtotal_payroll += total_payroll
				data.append(row)

		if filters.employee_details:
			total_row = ["<b> Total</b>","",total_present,""]
		else:
			total_row = ["<b> Total</b>","",total_present]
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

		if filters.hide_zero:
			colen = len(columns)
			x = 0
			while x < colen:
				if columns[x]['fieldname'] not in ["employee", "employee_name", "present_days", "position_title", "total_income", "total_deduction", "total_payroll"]:
					if totals[columns[x]['fieldname']] <= 0:
						del columns[x]
						if filters.include_header:
							row_num = 3
							if filters.location:
								row_num = 4
								
							for y,d in enumerate(data[row_num:]):
								del data[y+row_num][x]
						else:
							for y,d in enumerate(data):
								del data[y][x]
						colen -= 1
					else:
						x +=1
				else:
					x += 1


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
			"label": _("Employee" if not filters.include_header else ""),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 200 if filters.include_header else 120,
			"fieldlabel": "Employee",
			"hidden": 0
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name" if not filters.include_header else ""),
			"fieldtype": "Data",
			"width": 200,
			"fieldlabel": "Employee Name",
			"hidden": 0
		},
		{
			"fieldname": "present_days",
			"label": _("Present Days" if not filters.include_header else ""),
			"fieldtype": "Data",
			"width": 120,
			"fieldlabel": "Present Days",
			"hidden": 0
		},
	]
	
	if filters.employee_details:
		columns.append({
			"fieldname": "position_title",
			"label": _("Position Title" if not filters.include_header else ""),
			"fieldtype": "Data",
			"width": 200,
			"fieldlabel": "Position Title",
			"hidden": 0
			})

	income_types = frappe.db.sql_list(""" SELECT code
		FROM `tabTransaction Type` WHERE `type` = 'Income' ORDER BY sort """)

	deduction_types = frappe.db.sql_list(""" SELECT code
		FROM `tabTransaction Type` WHERE `type` = 'Deduction' ORDER BY sort""")

	if employee_list:
		for pay_code in income_types:	
			pay_title = frappe.db.get_value("Transaction Type", pay_code, 'title')
			columns.append({			
				"fieldname": pay_code,
				"label": pay_title if not filters.include_header else "",
				"fieldtype": "Data",
				"width": 100,
				"fieldlabel": pay_title,
				"hidden": 0
			})

		for pay_code in deduction_types:
			pay_title = frappe.db.get_value("Transaction Type", pay_code, 'title')
			columns.append({			
				"fieldname": pay_code,
				"label": pay_title if not filters.include_header else "",
				"fieldtype": "Data",
				"width": 100,
				"fieldlabel": pay_title,
				"hidden": 0
			})

	columns += [
		{
			"fieldname": "total_income",
			"label": _("Total Income" if not filters.include_header else ""),
			"fieldtype": "Data",
			"width": 100,
			"fieldlabel": "Total Income",
			"hidden": 0
		},
		{
			"fieldname": "total_deduction",
			"label": _("Total Deduction" if not filters.include_header else ""),
			"fieldtype": "Data",
			"width": 100,
			"fieldlabel": "Total Deduction",
			"hidden": 0
		},
		{
			"fieldname": "total_payroll",
			"label": _("Total Payroll" if not filters.include_header else ""),
			"fieldtype": "Data",
			"width": 100,
			"fieldlabel": "Total Payroll",
			"hidden": 0
		},
	]

	return columns, income_types, deduction_types

def get_employees(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql("""SELECT DISTINCT PR.employee, PR.employee_name, PR.present_days, TE.rate, TE.total_yr_days, TE.rate_type, TE.no_hours, TE.mth_percentage, TE.min_take_home, PR.net_payroll, PR.total_income, TE.position_title
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
		employees = frappe.db.sql("""SELECT DISTINCT PR.employee, PR.employee_name, PR.present_days, TE.rate, TE.total_yr_days, TE.rate_type, TE.no_hours, TE.mth_percentage, TE.min_take_home, PR.net_payroll, PR.total_income, TE.position_title
		FROM `tabPayroll Register` PR JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		WHERE PR.period = %(period)s
			AND PR.on_hold = 0
			AND PR.company = %(company)s {conditions} ORDER BY PR.employee_name""".format(conditions=get_conditions(filters)), { 
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
		conditions.append("PR.`location`=%(location)s")

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
