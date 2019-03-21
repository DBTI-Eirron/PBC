# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, calendar, time
from frappe.utils import cint, flt, getdate, cstr
from time import strptime
from frappe import _, msgprint

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "amount_compensation",
			"label": _("Amount Compensation"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "holiday_pay",
			"label": _("Holiday Pay"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "overtime_pay",
			"label": _("Overtime Pay"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "13th_month_pay",
			"label": _("13th Month Pay"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "de_minimis",
			"label": _("DE MINIMIS"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "statutory",
			"label": _("STATUTORY "),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "taxable_salary",
			"label": _("Taxable Salary "),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "sss_hdmf_phic",
			"label": _("SSS, HDMF, PHIC"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "wht",
			"label": _("WHT"),
			"fieldtype": "Data",
			"width": 180
		}
	]

	return columns

def get_data(filters):
	data = []

	if filters.month and filters.year:
		pay_from = str(filters.month)+"-01-"+filters.year
		pay_to = str(filters.month)+"-"+str(calendar.monthrange(int(filters.year), int(filters.month))[1])+"-"+filters.year
		pay_from = getdate(str(pay_from))
		pay_to = getdate(str(pay_to))

	employee_list = get_employees(filters, pay_from, pay_to)
	if employee_list:
		payreg_code_map = get_payreg_code_map(filters, employee_list)
		payreg_birtype_map = get_payreg_birtype_map(filters, employee_list)

		total_amount_compensation = 0.00
		total_holiday_pay = 0.00
		total_overtime_pay = 0.00
		total_month_pay = 0.00
		total_de_minimis = 0.00
		total_statutory = 0.00
		total_taxable_salary = 0.00
		total_sss_hdmf_phic = 0.00
		total_wht = 0.00

		for emp in employee_list:
			amount_compensation = 0.00
			holiday_pay = 0.00
			overtime_pay = 0.00
			month_pay = 0.00
			de_minimis = 0.00
			statutory = 0.00
			taxable_salary = 0.00
			sss_hdmf_phic = 0.00
			wht = 0.00

			emp_name = emp.employee_name
			amount_compensation = flt(emp.total_income, 8)
			holiday_pay = 0.00
			overtime_pay = flt(payreg_code_map.get(emp.name, {}).get("OT"), 8)
			month_pay = flt(payreg_birtype_map.get(emp.name, {}).get("13th Month"), 8)
			de_minimis = flt(payreg_birtype_map.get(emp.name, {}).get("Deminimis"), 8)
			statutory = flt(payreg_code_map.get(emp.name, {}).get("BS"), 8)
			taxable_salary = flt(emp.taxable_income, 8)
			sss_hdmf_phic += flt(payreg_code_map.get(emp.name, {}).get("SSS"), 8)
			sss_hdmf_phic += flt(payreg_code_map.get(emp.name, {}).get("HDMF"), 8)
			sss_hdmf_phic += flt(payreg_code_map.get(emp.name, {}).get("PHIC"), 8)
			wht = flt(payreg_code_map.get(emp.name, {}).get("WHTAX"), 8)

			row = {
				"employee_name": emp_name,
				"amount_compensation": '{:,.2f}'.format(amount_compensation),
				"holiday_pay": '{:,.2f}'.format(holiday_pay),
				"overtime_pay": '{:,.2f}'.format(overtime_pay),
				"13th_month_pay": '{:,.2f}'.format(month_pay),
				"de_minimis": '{:,.2f}'.format(de_minimis),
				"statutory": '{:,.2f}'.format(statutory),
				"taxable_salary": '{:,.2f}'.format(taxable_salary),
				"sss_hdmf_phic": '{:,.2f}'.format(sss_hdmf_phic),
				"wht": '{:,.2f}'.format(wht),
			}
			data.append(row)

			total_amount_compensation += amount_compensation
			total_holiday_pay += holiday_pay
			total_overtime_pay += overtime_pay
			total_month_pay += month_pay
			total_de_minimis += de_minimis
			total_statutory += statutory
			total_taxable_salary += taxable_salary
			total_sss_hdmf_phic += sss_hdmf_phic
			total_wht += wht

		row = {
			"employee_name": "",
			"amount_compensation": '{:,.2f}'.format(total_amount_compensation),
			"holiday_pay": '{:,.2f}'.format(total_holiday_pay),
			"overtime_pay": '{:,.2f}'.format(total_overtime_pay),
			"13th_month_pay": '{:,.2f}'.format(total_month_pay),
			"de_minimis": '{:,.2f}'.format(total_de_minimis),
			"statutory": '{:,.2f}'.format(total_statutory),
			"taxable_salary": '{:,.2f}'.format(total_taxable_salary),
			"sss_hdmf_phic": '{:,.2f}'.format(total_sss_hdmf_phic),
			"wht": '{:,.2f}'.format(total_wht),
		}
		data.append(row)

	return data

def get_employees(filters, pay_from, pay_to):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee, SUM(PR.total_income) as total_income, TE.`name`, SUM(PR.taxable_income) as taxable_income, PR.employee_name
			FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
			WHERE PR.company = %(company)s 
				AND PR.posting_date >= %(from_date)s
				AND PR.posting_date <= %(to_date)s
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s) 
			GROUP BY PR.`employee`
			ORDER BY PR.employee_name """,{ 
			"company": filters.company,
			"from_date": pay_from,
			"to_date": pay_to,
			"user": frappe.session.user
		}, as_dict=True)
	else:
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee, SUM(PR.total_income) as total_income, TE.`name`, SUM(PR.taxable_income) as taxable_income, PR.employee_name
			FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
			WHERE PR.company = %(company)s 
				AND PR.posting_date >= %(from_date)s
				AND PR.posting_date <= %(to_date)s
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
			GROUP BY PR.`employee`
			ORDER BY PR.employee_name """,{ 
				"company": filters.company,
				"from_date": pay_from,
				"to_date": pay_to,
			}, as_dict=True)

	return employees

def get_payreg_code_map(filters, employee_list):
	payreg_code = frappe.db.sql(""" SELECT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		INNER JOIN `tabTransaction Type` TT ON PRE.`pay_code` = TT.`name`
		WHERE PR.employee IN (%s) GROUP BY PRE.`name` """ %
		', '.join(['%s']*len(employee_list)), tuple([emp.name for emp in employee_list]), as_dict=1)

	payreg_code_map = {}
	for d in payreg_code:
		if getdate(filters.from_date) <= getdate(d.posting_date) <= getdate(filters.to_date):
			payreg_code_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
			if payreg_code_map[d.employee][d.pay_code]:
				payreg_code_map[d.employee][d.pay_code] += flt(d.amount, 2)
			else:
				payreg_code_map[d.employee][d.pay_code] = flt(d.amount, 2)

	return payreg_code_map

def get_payreg_birtype_map(filters, employee_list):
	paryreg_birtype = frappe.db.sql(""" SELECT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount, TT.bir_type
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		INNER JOIN `tabTransaction Type` TT ON PRE.`pay_code` = TT.`name`
		WHERE PR.employee IN (%s) GROUP BY PRE.`name` """ %
		', '.join(['%s']*len(employee_list)), tuple([emp.name for emp in employee_list]), as_dict=1)

	paryreg_birtype_map = {}
	for d in paryreg_birtype:
		if getdate(filters.from_date) <= getdate(d.posting_date) <= getdate(filters.to_date):
			paryreg_birtype_map.setdefault(d.employee, frappe._dict()).setdefault(d.bir_type, [])
			if paryreg_birtype_map[d.employee][d.bir_type]:
				paryreg_birtype_map[d.employee][d.bir_type] += flt(d.amount, 2)
			else:
				paryreg_birtype_map[d.employee][d.bir_type] = flt(d.amount, 2)

	return paryreg_birtype_map