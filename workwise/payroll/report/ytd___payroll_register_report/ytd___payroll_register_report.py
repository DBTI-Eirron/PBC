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
			row = {
				'employee': emp,
				'employee_name': employee_list[emp]['employee_name'],
				'present_days': employee_list[emp]['present_days'],
			}
			total_present += employee_list[emp]['present_days']
			total_income = 0.00
			i = 0
			for income in income_types:
				income_amount = flt(income_map.get(emp, {}).get(income), 8)
				income_total[i] += flt(income_amount, 8)
				row[income] = format_precision(income_amount, filters.value_precision)
				i += 1
			total_income += flt(employee_list[emp]['total_income'], 8)

			total_deduction = 0.00
			i = 0
			for deduction in deduction_types:
				deduction_amount = flt(deduction_map.get(emp, {}).get(deduction), 8)
				deduction_total[i] += flt(deduction_amount, 8)
				row[deduction] = format_precision(deduction_amount, filters.value_precision)
				i += 1
			total_deduction += flt(employee_list[emp]['total_deduction'], 8)

			total_payroll = flt(employee_list[emp]['net_payroll'], 8)
			if total_payroll < 0:
				total_payroll = 0.00
			
			row['total_income'] = format_precision(total_income, filters.value_precision)
			row['total_deduction'] = format_precision(total_deduction, filters.value_precision)
			row['total_payroll'] = format_precision(total_payroll, filters.value_precision)

			dtotal_income += flt(employee_list[emp]['total_income'], 8)
			dtotal_deduction += flt(employee_list[emp]['total_deduction'], 8)
			dtotal_payroll += flt(employee_list[emp]['net_payroll'], 8)
			data.append(row)

		total_row = {
			'employee': '<b> Total</b>',
			'employee_name': '',
			'present_days': total_present,
		}
		if filters.hide_zero:
			i = 0
			for income in income_types:
				if income_total[i] > 0:
					total_row[income] = format_precision(income_total[i], filters.value_precision)
					i += 1
				else:
					del columns[i+3]
					del income_total[i]
					for d in data:
						del d[income]
						
			inlen = i
			i = 0
			for deduction in deduction_types:
				if deduction_total[i] > 0:
					total_row[deduction] = format_precision(deduction_total[i], filters.value_precision)
					i += 1
				else:
					del columns[i+inlen+3]
					del deduction_total[i]
					for d in data:
						del d[deduction]
		else:
			i = 0
			for income in income_types:
				total_row[income] = format_precision(income_total[i], filters.value_precision)
				i += 1

			i = 0
			for deduction in deduction_types:
				total_row[deduction] = format_precision(deduction_total[i], filters.value_precision)
				i += 1

		data = sorted(data, key=lambda k: k['employee_name'])
		total_row['total_income'] = format_precision(dtotal_income, filters.value_precision)
		total_row['total_deduction'] = format_precision(dtotal_deduction, filters.value_precision)
		total_row['total_payroll'] = format_precision(dtotal_payroll, filters.value_precision)
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

def get_employees(filters, from_date, to_date):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql("""SELECT PR.employee, TE.full_name as employee_name, PR.present_days, PR.total_income, PR.total_deduction, PR.net_payroll
		FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		INNER JOIN `tabPayroll Period` PRY on PR.`period` = PRY.`name`
		INNER JOIN `tabPayroll Year` PRYY on PRY.`payroll_year` = PRYY.`name`
		WHERE TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s)
		AND PR.on_hold = 0
		AND (%(year)s = PRYY.`name`)
		AND PR.company = %(company)s {conditions} ORDER BY PR.employee_name""".format(conditions=get_conditions(filters)), { 
			"from_date": from_date,
			"to_date": to_date,
			"company": filters.company,
			"user": cur_user,
			"employee": filters.employee,
			"location": filters.location,
			"year": filters.payroll_year
		}, as_dict=1)

	else:
		employees = frappe.db.sql("""SELECT PR.employee, TE.full_name as employee_name, PR.present_days, PR.total_income, PR.total_deduction, PR.net_payroll
		FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		INNER JOIN `tabPayroll Period` PRY on PR.`period` = PRY.`name`
		INNER JOIN `tabPayroll Year` PRYY on PRY.`payroll_year` = PRYY.`name`
		WHERE PR.on_hold = 0
		AND (%(year)s = PRYY.`name`)
		AND PR.company = %(company)s {conditions} ORDER BY PR.employee_name""".format(conditions=get_conditions(filters)), { 
			"from_date": from_date,
			"to_date": to_date,
			"company": filters.company,
			"employee": filters.employee,
			"location": filters.location,
			"year": filters.payroll_year
		}, as_dict=1)

	employee_map = {}
	for emp in employees:
		if emp.employee not in employee_map:
			employee_map.setdefault(emp.employee, frappe._dict({'employee_name':emp.employee_name, 'present_days':0.0, 'total_income':0.0, 'total_deduction':0.0, 'net_payroll': 0.00}))
		employee_map[emp.employee]['present_days'] += emp.present_days
		employee_map[emp.employee]['total_income'] += emp.total_income
		employee_map[emp.employee]['total_deduction'] += emp.total_deduction
		if emp.net_payroll > 0:
			employee_map[emp.employee]['net_payroll'] += emp.net_payroll

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
		INNER JOIN `tabPayroll Period` PRY on PR.`period` = PRY.`name`
		INNER JOIN `tabPayroll Year` PRYY on PRY.`payroll_year` = PRYY.`name`
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
		INNER JOIN `tabPayroll Period` PRY on PR.`period` = PRY.`name`
		INNER JOIN `tabPayroll Year` PRYY on PRY.`payroll_year` = PRYY.`name`
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
