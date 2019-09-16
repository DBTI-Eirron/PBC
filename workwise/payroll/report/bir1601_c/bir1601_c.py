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
	data = get_data(filters, columns)
	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Data",
			"width": 140
		},
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

def get_data(filters, columns):
	data = []
	emp_entries = {}

	if filters.month and filters.year:
		pay_from = filters.year+"-"+str(filters.month)+"-01"
		pay_to = filters.year+"-"+str(filters.month)+"-"+str(calendar.monthrange(int(filters.year), int(filters.month))[1])
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
			if emp.employee not in emp_entries:
				emp_entries[emp.employee] = {
					"employee_name": cstr(emp.full_name),
					"amount_compensation": 0.00,
					"taxable_salary": 0.00,
					"holiday_pay": 0.00,
					"overtime_pay": 0.00,
					"13th_month_pay": 0.00,
					"de_minimis": 0.00,
					"statutory": 0.00,
					"taxable_salary": 0.00,
					"sss_hdmf_phic": 0.00,
					"wht": 0.00,
					"included_payreg": []
				}

			if emp.payreg not in emp_entries[emp.employee]["included_payreg"]:
				emp_entries[emp.employee]["amount_compensation"] += flt(emp['total_income'] , 8)
				emp_entries[emp.employee]["taxable_salary"] += flt(emp['taxable_income'] , 8)
				emp_entries[emp.employee]["included_payreg"].append(emp.payreg)

			bir_type = tr_map[emp["pay_code"]]['bir_type']
			tr_type = tr_map[emp["pay_code"]]['type']
			is_taxable = tr_map[emp["pay_code"]]['is_taxable']

			if tr_type != "None":
				if bir_type == "Overtime" and tr_type == "Income":
					emp_entries[emp.employee]["overtime_pay"] += emp['amount']
				if bir_type == "Overtime" and tr_type == "Deduction":
					emp_entries[emp.employee]["overtime_pay"] -= emp['amount']
				if bir_type == "Holiday" and tr_type == "Income":
					emp_entries[emp.employee]["holiday_pay"] += emp['amount']
				if bir_type == "Holiday" and tr_type == "Deduction":
					emp_entries[emp.employee]["holiday_pay"] -= emp['amount']
				if bir_type == "13th Month" and tr_type == "Income":
					emp_entries[emp.employee]["13th_month_pay"] += emp['amount']
				if bir_type == "13th Month" and tr_type == "Deduction":
					emp_entries[emp.employee]["13th_month_pay"] -= emp['amount']
				if bir_type == "Deminimis" and tr_type == "Income":
					emp_entries[emp.employee]["de_minimis"] += emp['amount']
				if bir_type == "Deminimis" and tr_type == "Deduction":
					emp_entries[emp.employee]["de_minimis"] -= emp['amount']
				if emp['pay_code'] == "SSS":
					emp_entries[emp.employee]["sss_hdmf_phic"] += emp['amount']
				if emp['pay_code'] == "HDMF":
					emp_entries[emp.employee]["sss_hdmf_phic"] += emp['amount']
				if emp['pay_code'] == "PHIC":
					emp_entries[emp.employee]["sss_hdmf_phic"] += emp['amount']
				if emp['pay_code'] == "WHTAX":
					emp_entries[emp.employee]["wht"] += emp['amount']
				if emp['daily_rate'] <= emp['min_wage']:
					if bir_type == "Basic" and tr_type == "Income":
						emp_entries[emp.employee]["statutory"] += emp['amount']
					if bir_type == "Basic" and tr_type == "Deduction":
						emp_entries[emp.employee]["statutory"] -= emp['amount']

		for e in emp_entries:
			row = {
				"employee": e,
				"employee_name": emp_entries[e]["employee_name"],
				"amount_compensation": '{:,.2f}'.format( flt(emp_entries[e]["amount_compensation"], 2) ),
				"holiday_pay": '{:,.2f}'.format( flt(emp_entries[e]["holiday_pay"], 2) ),
				"overtime_pay": '{:,.2f}'.format( flt(emp_entries[e]["overtime_pay"], 2) ),
				"13th_month_pay": '{:,.2f}'.format( flt(emp_entries[e]["13th_month_pay"], 2) ),
				"de_minimis": '{:,.2f}'.format( flt(emp_entries[e]["de_minimis"], 2) ),
				"statutory": '{:,.2f}'.format( flt(emp_entries[e]["statutory"], 2) ),
				"taxable_salary": '{:,.2f}'.format( flt(emp_entries[e]["taxable_salary"], 2) ),
				"sss_hdmf_phic": '{:,.2f}'.format( flt(emp_entries[e]["sss_hdmf_phic"], 2) ),
				"wht": '{:,.2f}'.format( flt(emp_entries[e]["wht"], 2) ),
			}
			data.append(row)

			total_amount_compensation += flt(emp_entries[e]["amount_compensation"] , 8)
			total_holiday_pay += flt(emp_entries[e]["holiday_pay"] , 8)
			total_overtime_pay += flt(emp_entries[e]["overtime_pay"] , 8)
			total_month_pay += flt(emp_entries[e]["13th_month_pay"] , 8)
			total_de_minimis += flt(emp_entries[e]["de_minimis"] , 8)
			total_statutory += flt(emp_entries[e]["statutory"] , 8)
			total_taxable_salary += flt(emp_entries[e]["taxable_salary"] , 8)
			total_sss_hdmf_phic += flt(emp_entries[e]["sss_hdmf_phic"] , 8)
			total_wht += flt(emp_entries[e]["wht"] , 8)

		data = sorted(data, key = lambda k:k['employee_name'])

		total_row = {
			"employee": "",
			"employee_name": "",
			"amount_compensation": '{:,.2f}'.format( flt(total_amount_compensation, 2) ),
			"holiday_pay": '{:,.2f}'.format( flt(total_holiday_pay, 2) ),
			"overtime_pay": '{:,.2f}'.format( flt(total_overtime_pay, 2) ),
			"13th_month_pay": '{:,.2f}'.format( flt(total_month_pay, 2) ),
			"de_minimis": '{:,.2f}'.format( flt(total_de_minimis, 2) ),
			"statutory": '{:,.2f}'.format( flt(total_statutory, 2) ),
			"taxable_salary": '{:,.2f}'.format( flt(total_taxable_salary, 2) ),
			"sss_hdmf_phic": '{:,.2f}'.format( flt(total_sss_hdmf_phic, 2) ),
			"wht": '{:,.2f}'.format( flt(total_wht, 2) ),
		}
		data.append(total_row)

		if filters.hide_zero:
			total_rows = ["amount_compensation", "holiday_pay", "overtime_pay", "13th_month_pay", "de_minimis", "statutory", "taxable_salary", "sss_hdmf_phic", "wht"]
			max_range = len(total_row)
			idx = 2
			for x in total_rows:
				if flt(total_row[x], 2) <= 0:
					del columns[idx]
					idx -= 1
				idx += 1

	return data

def get_employees(filters, pay_from, pay_to):
	employees = frappe.db.sql("""SELECT PRE.`name`, PRE.`pay_code`, PRE.`amount`, PR.`name` as payreg, PR.`total_income`, 
		PR.`taxable_income`, PR.`employee`, TE.`full_name`, PR.`daily_rate`, TL.`name` as location, TL.`min_wage`
		FROM `tabPayroll Register Entries` PRE
		INNER JOIN `tabPayroll Register` PR ON PRE.`parent` = PR.`name`
		INNER JOIN `tabEmployee` TE ON PR.`employee` = TE.`name`
		INNER JOIN `tabLocation` TL ON TE.`location` = TL.`name`
		WHERE TE.is_active = 1
		AND PR.company = %(company)s 
		AND (PR.posting_date BETWEEN %(from_date)s AND %(to_date)s)
		{conditions}
		GROUP BY PRE.`name` """.format(conditions=get_conditions(filters)),{ 
		"company": filters.company,
		"from_date": getdate(pay_from),
		"to_date": getdate(pay_to),
	}, as_dict=True)

	return employees

def get_conditions(filters):
	conditions = []
	if filters.employee:
		conditions.append(_("PR.`employee` = '{0}'").format(filters.employee))

	if frappe.session.user != "Administrator":
		conditions.append(_("TE.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 