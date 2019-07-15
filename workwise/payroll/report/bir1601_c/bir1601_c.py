# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, calendar, time
from frappe.utils import cint, flt, getdate, cstr
from time import strptime
from frappe import _, msgprint
from workwise.payroll.payroll_utils import get_transaction_map

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
	tr_map = get_transaction_map()
	if employee_list:
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

			salary = frappe.db.sql("""SELECT pr.employee, pr.employee_name, pre.pay_code, pre.amount FROM `tabPayroll Register` pr
			INNER JOIN `tabPayroll Register Entries` pre ON pre.parent = pr.`name`
			WHERE  pr.company = %s AND pr.employee = %s AND pr.posting_date >= %s AND pr.posting_date <= %s """,(filters.company, emp.name, pay_from, pay_to), as_dict=True)

			for d in salary:
				bir_type = tr_map[d.get("pay_code")]['bir_type']
				tr_type = tr_map[d.get("pay_code")]['type']
				is_taxable = tr_map[d.get("pay_code")]['is_taxable']

				if tr_type != "None":
					if bir_type == "Overtime" and tr_type == "Income":
						overtime_pay += d.amount
					if bir_type == "Overtime" and tr_type == "Deduction":
						overtime_pay -= d.amount
					if bir_type == "Holiday" and tr_type == "Income":
						holiday_pay += d.amount
					if bir_type == "Holiday" and tr_type == "Deduction":
						holiday_pay -= d.amount
					if bir_type == "13th Month" and tr_type == "Income":
						month_pay += d.amount
					if bir_type == "13th Month" and tr_type == "Deduction":
						month_pay -= d.amount
					if bir_type == "Deminimis" and tr_type == "Income":
						de_minimis += d.amount
					if bir_type == "Deminimis" and tr_type == "Deduction":
						de_minimis -= d.amount
					if bir_type == "Basic" and tr_type == "Income":
						statutory += d.amount
					if bir_type == "Basic" and tr_type == "Deduction":
						statutory -= d.amount
					if d.pay_code == "SSS":
						sss_hdmf_phic += d.amount
					if d.pay_code == "HDMF":
						sss_hdmf_phic += d.amount
					if d.pay_code == "PHIC":
						sss_hdmf_phic += d.amount
					if d.pay_code == "WHTAX":
						wht += d.amount

				emp_name = emp.employee_name
				amount_compensation = emp.total_income	
				taxable_salary = emp.taxable_income

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

		total_row = {
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
		data.append(total_row)

	return data

def get_employees(filters, pay_from, pay_to):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql("""SELECT DISTINCT TE.name, SUM(PR.total_income) as total_income, TE.`name`, SUM(PR.taxable_income) as taxable_income, PR.employee_name
			FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
			WHERE TE.is_active = 1
				AND PR.company = %(company)s 
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
		employees = frappe.db.sql(""" SELECT DISTINCT TE.name, SUM(PR.total_income) as total_income, TE.`name`, SUM(PR.taxable_income) as taxable_income, PR.employee_name
			FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
			WHERE TE.is_active = 1
				AND PR.company = %(company)s 
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