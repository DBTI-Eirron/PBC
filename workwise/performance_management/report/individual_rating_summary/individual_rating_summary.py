# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	#initial data
	data = []
	years = get_payroll_year(filters)
	for year in years:
		data.append({"year":year.name})
		employees = get_employees(filters,year)
		for emp in employees:
			row = []
			row = {"employee":emp.appraisee,"employee_name":emp.appraisee_name}
			if filters.year:
				periods = get_appraisal_period(filters,year.name)
				for period in periods:
					total = get_emp_total(filters,period,emp.appraisee)
					row.update({period.period_name:total})
			ctotal = get_emp_total(filters,year,emp.appraisee)
			row.update({"total":'{:,.2f}'.format(flt(ctotal))})
			data.append(row)
		#subtotal

		if filters.year:
			periods = get_appraisal_period(filters,year.name)
			row = []
			row = {"employee_name":"Total"}
			for period in periods:
				total = get_total(filters,period)
				row.update({period.period_name:total})
			ctotal = get_total(filters,year)
			row.update({"total":'{:,.2f}'.format(flt(ctotal))})
			data.append(row)
		else:
			row = []
			row = {"employee_name":"Total"}
			ctotal = get_total(filters,year)
			row.update({"total":'{:,.2f}'.format(flt(ctotal))})
			data.append(row)

	if filters.year is None:
		row = []
		row = {"employee_name":"Grand Total"}
		ctotal = get_grand_total(filters)
		row.update({"total":'{:,.2f}'.format(flt(ctotal))})
		data.append(row)

	return data

def get_columns(filters):
	columns = [
		{
			"fieldname": "year",
			"label": _("Year"),
			"fieldtype": "Data",
			"width": 80
		},
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 150
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 180
		},
	]
	if filters.year:
		periods = get_appraisal_period(filters,filters.year)
		for d in periods:
			columns += [
				{
					"fieldname": d.period_name,
					"label": _(d.period_name),
					"fieldtype": "Data",
					"width": 120
				},
			]
	columns += [
		{
			"fieldname": "total",
			"label": _("Total"),
			"fieldtype": "Data",
			"width": 120
		},
	]


	return columns

def get_employees(filters,period):
	if filters.employee:
		employees = frappe.db.sql("""SELECT DISTINCT `appraisee`, appraisee_name FROM `tabAppraisal` WHERE docstatus = 1  AND `from_date` >= %s AND `to_date` <= %s AND company = %s AND appraisee = %s""",(period.from_date,period.to_date,filters.company,filters.employee),as_dict=True)
	else:
		employees = frappe.db.sql("""SELECT DISTINCT `appraisee`, appraisee_name FROM `tabAppraisal` WHERE docstatus = 1  AND `from_date` >= %s AND `to_date` <= %s AND company = %s""",(period.from_date,period.to_date,filters.company),as_dict=True)
	return employees

def get_appraisal_period(filters,year):
	periods = frappe.db.sql("""SELECT `period_name`,from_date,to_date FROM `tabTarget Setting Period` WHERE `payroll_year` = %s""",(year),as_dict=True)
	return periods

def get_payroll_year(filters):
	if filters.year:
		years = frappe.db.sql("""SELECT `name`,from_date,to_date FROM `tabPayroll Year` WHERE `name` = %s""",(filters.year),as_dict=True)
	else:	
		years = frappe.db.sql("""SELECT `name`,from_date,to_date FROM `tabPayroll Year`""",as_dict=True)
	return years

def get_emp_total(filters,period,employee):
	total = frappe.db.sql("""SELECT AVG(total_score) as average FROM `tabAppraisal` WHERE `from_date` >= %s AND `to_date` <= %s AND appraisee = %s""",(period.from_date,period.to_date,employee),as_dict=True)
	if total:
		return total[0].average
	else:
		return 0

def get_total(filters,period):
	total = frappe.db.sql("""SELECT AVG(total_score) as average FROM `tabAppraisal` WHERE `from_date` >= %s AND `to_date` <= %s and company = %s""",(period.from_date,period.to_date,filters.company),as_dict=True)
	if total:
		return total[0].average
	else:
		return 0

def get_grand_total(filters):
	total = frappe.db.sql("""SELECT AVG(total_score) as average FROM `tabAppraisal` WHERE company = %s""",(filters.company),as_dict=True)
	if total:
		return total[0].average
	else:
		return 0