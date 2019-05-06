	# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, getdate, cstr
from frappe import _, msgprint


def execute(filters=None):
	validate_filters(filters)
	data =  get_data(filters)
	columns = get_columns(filters)
	return columns, data

def get_data(filters):
	data = []
	employee_list = get_employees(filters)
	register_map = get_PHIC_map(filters, employee_list)
	PHIC_types = ["PHIC","PHICE"]
	total_ee = 0.00
	total_er =0.00
	for emp in employee_list:
		emp_cont = 0.00
		er_cont = 0.00
		result = []
		for d in PHIC_types:
			PHIC_amount = flt(register_map.get(emp.name, {}).get(d))
			result.append(PHIC_amount)
		emp_cont = flt(result[0])
		er_cont = flt(result[1])
		if emp_cont > 0 or er_cont > 0:
			status = get_status(emp,filters)
			row = {'phic_no':emp.phic_no, 'monthly_rate':emp.rate, 'employee_name':emp.full_name, 'employee_status':status, 'date_hired':(emp.date_hired).strftime('%m/%d/%Y'), 'birth_day':(emp.birthday).strftime('%m/%d/%Y')}
			row.update({'employee':emp_cont,'employer':er_cont})
			total_ee += emp_cont
			total_er += er_cont	
			data.append(row)
	return data

def get_columns(filters):
	columns = [
		{
		"fieldname": "phic_no",
		"label": _("PHIC Number"),
		"fieldtype": "Data",
		"width": 170
		},{
		"fieldname": "monthly_rate",
		"label": _("Monthly Rate"),
		"fieldtype": "Data",
		"width": 100
		},{
		"fieldname": "employee_name",
		"label": _("Employee Name"),
		"fieldtype": "Data",
		"width": 120
		},{
		"fieldname": "employee_status",
		"label": _("Employee Status"),
		"fieldtype": "Data",
		"width": 120
		},{
		"fieldname": "date_hired",
		"label": _("Date of Hired"),
		"fieldtype": "Data",
		"width": 120
		},{
		"fieldname": "birth_day",
		"label": _("Date of Birth"),
		"fieldtype": "Data",
		"width": 100
		},{
		"fieldname": "employee",
		"label": _("Employee"),
		"fieldtype": "Data",
		"width": 100
		},{
		"fieldname": "employer",
		"label": _("Employer"),
		"fieldtype": "Data",
		"width": 100
		}, 
	]

	return columns

def get_employees(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee as `name`, TE.full_name as full_name, TE.phic_no, TE.rate, TE.is_active, TE.date_hired, TE.birthday FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
				WHERE PR.company = %(company)s 
				AND PR.posting_date >= %(from_date)s
				AND PR.posting_date <= %(to_date)s
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s)
				GROUP BY PR.employee
				ORDER BY PR.employee_name """,{ 
				"company": filters.company,
				"from_date": filters.from_date,
				"to_date": filters.to_date,
				"user": frappe.session.user
			}, as_dict=True)
	else:
		employees = frappe.db.sql(""" SELECT DISTINCT PR.employee as `name`, TE.full_name as full_name, TE.phic_no, TE.rate, TE.is_active, TE.date_hired, TE.birthday FROM `tabPayroll Register` PR INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
				WHERE PR.company = %(company)s 
				AND PR.posting_date >= %(from_date)s
				AND PR.posting_date <= %(to_date)s
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
				GROUP BY PR.employee
				ORDER BY PR.employee_name """,{ 
				"company": filters.company,
				"from_date": filters.from_date,
				"to_date": filters.to_date
			}, as_dict=True)

	return employees

def get_PHIC_map(filters, employee_list):
	PHIC_details = frappe.db.sql(""" SELECT DISTINCT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		WHERE employee in (%s) GROUP BY PRE.`name` """ %
		', '.join(['%s']*len(employee_list)), tuple([emp.name for emp in employee_list]), as_dict=1)

	PHIC_map = {}
	for d in PHIC_details:
		if getdate(filters.from_date) <= getdate(d.posting_date) <= getdate(filters.to_date):
			PHIC_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
			if PHIC_map[d.employee][d.pay_code]:
				PHIC_map[d.employee][d.pay_code] += flt(d.amount, 2)
			else:
				PHIC_map[d.employee][d.pay_code] = flt(d.amount, 2)

	return PHIC_map

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

def get_status(emp,filters):
	if emp.is_active:
		value = frappe.db.sql("""SELECT SUM(PR.`net_payroll`) as `value` FROM `tabPayroll Register` PR INNER JOIN `tabPayroll Period` PP ON PR.period = PP.`name` WHERE PR.employee = %s and PP.from_date >= %s and PP.to_date <= %s""",(emp.name,filters.from_date,filters.to_date),as_dict=True)
		if value[0].value < 0:
			return "NE"
		else:
			return "A"
	else:
		return "S"