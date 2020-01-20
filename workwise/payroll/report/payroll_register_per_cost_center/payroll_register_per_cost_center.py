# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	validate_filters(filters)
	cost_center_list = get_cost_center(filters)
	income_types = []
	deduction_types = []
	data = []
		
	income_types = frappe.db.sql_list(""" SELECT code FROM `tabTransaction Type` WHERE `type` = 'Income' ORDER BY sort """)
	deduction_types = frappe.db.sql_list(""" SELECT code FROM `tabTransaction Type` WHERE `type` = 'Deduction' ORDER BY sort""")

	columns = get_columns(income_types, deduction_types)
	
	final_total_row = ["<b> Total</b>",""]
	f_total_income, f_total_deduction, f_total_payroll = 0, 0, 0
	f_income_total, f_deduction_total = [], []
	if filters.include_header:
		data.append(["<b>"+filters.company+"</b>"])
		data.append(["<b>"+filters.payroll_period+"</b>"])
		if filters.location:
			data.append(["<b>"+filters.location+"</b>"])
		if filters.cost_center:
			data.append(["<b>"+"Cost Center: "+filters.cost_center+"</b>"])
		data.append({})
		header = []
		for col in columns:
			header.append(col['label'])
		data.append(header)
	for f_income in income_types:
		f_income_total.append(0)

	for f_deduction in deduction_types:
		f_deduction_total.append(0)

	for cost_cent in cost_center_list:
		cost_name = "<b>"+ cstr(cost_cent.name) +"</b>"
		employee_list = get_employees(filters, cost_cent.name)
		if employee_list:
			data.append([cost_name])
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
					row.append(format_precision(income_amount, filters.value_precision))
					i += 1

				i = 0
				for deduction in deduction_types:
					deduction_amount = flt(deduction_map.get(emp.employee, {}).get(deduction), 8)
					total_deduction += flt(deduction_amount, 8)
					deduction_total[i] += flt(deduction_amount, 8)
					row.append(format_precision(deduction_amount, filters.value_precision))
					i += 1

				total_payroll = flt(total_income, 8) - flt(total_deduction, 8)
				row += [format_precision(total_income, filters.value_precision), format_precision(total_deduction, filters.value_precision), format_precision(total_payroll, filters.value_precision)]
				dtotal_income += flt(total_income, 2)
				dtotal_deduction += flt(total_deduction, 2)
				dtotal_payroll += flt(total_payroll, 2)
				data.append(row)

			i = 0
			for income in income_types:
				total_row.append(format_precision(income_total[i], filters.value_precision))
				f_income_total[i] += flt(income_total[i], 8)
				i += 1

			i = 0
			for deduction in deduction_types:
				total_row.append(format_precision(deduction_total[i], filters.value_precision))
				f_deduction_total[i] += flt(deduction_total[i], 8)
				i += 1

			total_row += [format_precision(dtotal_income, filters.value_precision), format_precision(dtotal_deduction, filters.value_precision), format_precision(dtotal_payroll, filters.value_precision)]
			f_total_income += flt(dtotal_income, 2)
			f_total_deduction += flt(dtotal_deduction, 2)
			f_total_payroll += flt(dtotal_payroll, 2)
			data.append(total_row)

	#Final Total
	i = 0
	for income in income_types:
		final_total_row.append(format_precision(f_income_total[i], filters.value_precision))
		i += 1
	i = 0
	for deduction in deduction_types:
		final_total_row.append(format_precision(f_deduction_total[i], filters.value_precision))
		i += 1
	final_total_row += [format_precision(f_total_income, filters.value_precision), format_precision(f_total_deduction, filters.value_precision), format_precision(f_total_payroll, filters.value_precision)]
	data.append("")

	if filters.hide_zero:
		max_range = len(final_total_row)
		idx = 0
		for x in xrange(0,max_range):
			if final_total_row[idx] == format_precision(0, filters.value_precision):
				del final_total_row[idx]
				del columns[idx]
				for d in data:
					if len(d) > 1:
						del d[idx]
			else:
				idx += 1
				
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

	return columns

def get_employees(filters, cost_center):


	employees = frappe.db.sql("""SELECT PR.employee, PR.employee_name
	FROM `tabPayroll Register` PR JOIN `tabEmployee` TE ON PR.employee = TE.`name`
	WHERE PR.period = %(period)s
	AND PR.on_hold = 0
	AND TE.company = %(company)s
	AND TE.cost_center = %(cost_center)s
	{conditions} ORDER BY PR.employee_name""".format(conditions=get_conditions(filters)), { 
		"period": filters.payroll_period,
		"company": filters.company,
		"employee": filters.employee,
		"cost_center": cost_center,
	}, as_dict=1)

	return employees

def get_cost_center(filters):
	conditions = ""
	if filters.get("cost_center"):
		lft, rgt = frappe.db.get_value("Cost Center", filters.cost_center, ["lft", "rgt"])
		conditions = " AND ( `lft` BETWEEN '{0}' AND '{1}' )".format(lft, rgt)

	cost_center = frappe.db.sql("""SELECT `name` FROM `tabCost Center` WHERE `parent` = %(company)s {conditions} """.format(conditions=conditions), { 
		"company": filters.company
		}, as_dict=1)

	return cost_center

def get_conditions(filters):
	conditions = []
	if frappe.session.user != "Administrator":
		conditions.append(_("TE.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

	if filters.get("employee"):
		conditions.append("TE.`name`=%(employee)s")

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

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