# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	validate_filters(filters)
	department_list = get_department(filters)
	income_types = []
	deduction_types = []
	data = []
		
	income_types = frappe.db.sql_list(""" SELECT code FROM `tabTransaction Type` WHERE `type` = 'Income' ORDER BY code """)
	deduction_types = frappe.db.sql_list(""" SELECT code FROM `tabTransaction Type` WHERE `type` = 'Deduction' ORDER BY code""")

	columns = get_columns(income_types, deduction_types)
	
	final_total_row = ["<b> Total</b>",""]
	f_total_income, f_total_deduction, f_total_payroll = 0, 0, 0
	f_income_total, f_deduction_total = [], []

	for f_income in income_types:
		f_income_total.append(0)

	for f_deduction in deduction_types:
		f_deduction_total.append(0)

	for department in department_list:
		dept_name = "<b>"+ str(department.name) +"</b>"
		employee_list = get_employees(filters, department.name)
		if employee_list:
			data.append([dept_name])
			income_map = get_income_map(filters, employee_list)
			deduction_map = get_deduction_map(filters, employee_list)
			dtotal_income, dtotal_deduction, dtotal_payroll = 0, 0, 0
			income_total, deduction_total = [], []
			total_row = ["<b> Total</b>",""]

			for income in income_types:
				income_total.append(0)

			for deduction in deduction_types:
				deduction_total.append(0)

			for emp in employee_list:
				row = [emp.employee, emp.employee_name]
				total_payroll, total_income, total_deduction = 0, 0, 0

				i = 0
				for income in income_types:
					income_amount = flt(income_map.get(emp.employee, {}).get(income), 8)
					total_income += flt(income_amount, 8)
					income_total[i] += flt(income_amount, 8)
					row.append(income_amount)
					i += 1

				i = 0
				for deduction in deduction_types:
					deduction_amount = flt(deduction_map.get(emp.employee, {}).get(deduction), 8)
					total_deduction += flt(deduction_amount, 8)
					deduction_total[i] += flt(deduction_amount, 8)
					row.append(deduction_amount)
					i += 1

				total_payroll = flt(total_income, 8) - flt(total_deduction, 8)
				row += [flt(total_income, 2), flt(total_deduction, 2), flt(total_payroll, 2)]
				dtotal_income += flt(total_income, 2)
				dtotal_deduction += flt(total_deduction, 2)
				dtotal_payroll += flt(total_payroll, 2)
				data.append(row)

			i = 0
			for income in income_types:
				total_row.append(income_total[i])
				f_income_total[i] += flt(income_total[i], 8)
				i += 1

			i = 0
			for deduction in deduction_types:
				total_row.append(deduction_total[i])
				f_deduction_total[i] += flt(deduction_total[i], 8)
				i += 1

			total_row += [flt(dtotal_income, 2), flt(dtotal_deduction, 2), flt(dtotal_payroll, 2)]
			f_total_income += flt(dtotal_income, 2)
			f_total_deduction += flt(dtotal_deduction, 2)
			f_total_payroll += flt(dtotal_payroll, 2)

			data.append(total_row)

	#Final Total
	if not filters.department:
		i = 0
		for income in income_types:
			final_total_row.append(f_income_total[i])
			i += 1
		i = 0
		for deduction in deduction_types:
			final_total_row.append(f_deduction_total[i])
			i += 1
		final_total_row += [flt(f_total_income, 2), flt(f_total_deduction, 2), flt(f_total_payroll, 2)]
		data.append("")
		data.append(final_total_row)

	return columns, data

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

def get_columns(income_types, deduction_types):
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
	]

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
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "total_deduction",
			"label": _("Total Deduction"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "total_payroll",
			"label": _("Total Payroll"),
			"fieldtype": "Currency",
			"width": 100
		},
	]

	return columns

def get_employees(filters, department):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql("""SELECT DISTINCT PR.employee, PR.employee_name
		FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		WHERE TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s)
			AND PR.period = %(period)s
			AND PR.company = %(company)s
			AND TE.department = '{department}' 
			{conditions}
			AND PR.on_hold = 0 AND TE.is_active = 1 ORDER BY PR.employee_name""".format(conditions=get_conditions(filters), department=department), { 
				"period": filters.payroll_period,
				"company": filters.company,
				"user": cur_user,
				"employee": filters.employee,
				"department": filters.department
			}, as_dict=1)
	else:
		employees = frappe.db.sql("""SELECT DISTINCT PR.employee, PR.employee_name
		FROM `tabPayroll Register` PR JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		WHERE PR.period = %(period)s
			AND TE.company = %(company)s 
			AND TE.department = '{department}'
			{conditions}
			AND PR.on_hold = 0 AND TE.is_active = 1 ORDER BY PR.employee_name""".format(conditions=get_conditions(filters), department=department), { 
				"period": filters.payroll_period,
				"company": filters.company,
				"employee": filters.employee,
				"department": filters.department
			}, as_dict=1)

	return employees

def get_department(filters):
	department = frappe.db.sql("""SELECT `name` FROM tabDepartment ORDER BY lft """, filters, as_dict=1)
	return department

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("TE.`name`=%(employee)s")
		
	if filters.get("department"):
		conditions.append("TE.department=%(department)s")

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
		WHERE PR.on_hold = 0 AND PR.period = %s AND employee in (%s) GROUP BY PRE.`name` """ %
		('%s',', '.join(['%s']*len(employee_list))), tuple([filters.payroll_period] + [emp.employee for emp in employee_list]), as_dict=1)

	deduction_map = {}
	for d in deduction_details:
		deduction_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
		if deduction_map[d.employee][d.pay_code]:
			deduction_map[d.employee][d.pay_code] += flt(d.amount, 8)
		else: 
			deduction_map[d.employee][d.pay_code] = flt(d.amount, 8)

	return  deduction_map