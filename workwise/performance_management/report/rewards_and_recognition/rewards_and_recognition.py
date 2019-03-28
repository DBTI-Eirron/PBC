# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [{
		"fieldname":"employee",
		"label": _("Employee"),
		"fieldtype": "Data",
		"width": 160
	},{
		"fieldname":"employee_name",
		"label": _("Employee Name"),
		"fieldtype": "Data",
		"width": 160
	},{
		"fieldname":"department",
		"label": _("Department"),
		"fieldtype": "Data",
		"width": 160
	}]
	year_division = get_division(filters)
	for date in year_division:
		columns.append({
		"fieldname":str(date['from_date']),
		"label": _(date['from_date'].strftime("%b")+"-"+date['to_date'].strftime("%b")),
		"fieldtype": "Data",
		"width": 160
		})
	return columns

def get_data(filters):
	data = []
	rating_class = frappe.db.sql("""SELECT * FROM `tabRating Classification`""",as_dict=True)
	year_division = get_division(filters)
	start_date,end_date = get_year_start_end(filters)
	employee = frappe.db.sql("""SELECT appraisee, appraisee_name, department FROM `tabAppraisal` WHERE company = %s AND docstatus = 1 AND from_date BETWEEN %s AND %s""",(filters.company,start_date,end_date),as_dict=True)
	for emp in employee:
		row = {'employee':emp.appraisee,'employee_name':emp.appraisee_name,'department':emp.department}
		for div in year_division:
			ee = 0
			average = frappe.db.sql("""SELECT AVG(total_score) as average FROM `tabAppraisal` WHERE company = %s AND docstatus = 1 AND from_date BETWEEN %s AND %s""",(filters.company,div['from_date'],div['to_date']),as_dict=True)
			for rating in rating_class:
				if average[0].average >= rating.rate_from and average[0].average >= rating.rate_to:
					if rating.rating_equivalent == "Exceeds Expectation(EE)":
						row.update({str(div['from_date']):rating.rating_equivalent})
						ee += 1
		if ee > 0:
			data.append(row)
	# frappe.throw(_(data))
	return data

def get_division(filters):
	if filters.period == "Yearly":
		from_date = datetime.strptime(filters.payroll_year+"-01-01",'%Y-%m-%d')
		to_date = datetime.strptime(filters.payroll_year+"-12-31",'%Y-%m-%d')
		result = [{'from_date':from_date,'to_date':to_date}]
	elif filters.period == "Half-Yearly":
		from_date1 = datetime.strptime(filters.payroll_year+"-01-01",'%Y-%m-%d')
		to_date1 = datetime.strptime(filters.payroll_year+"-06-30",'%Y-%m-%d')
		from_date2 = datetime.strptime(filters.payroll_year+"-07-01",'%Y-%m-%d')
		to_date2 = datetime.strptime(filters.payroll_year+"-12-31",'%Y-%m-%d')
		result = [{'from_date':from_date1,'to_date':to_date1},{'from_date':from_date2,'to_date':to_date2}]
	elif filters.period == "Quarterly":
		from_date1 = datetime.strptime(filters.payroll_year+"-01-01",'%Y-%m-%d')
		to_date1 = datetime.strptime(filters.payroll_year+"-03-31",'%Y-%m-%d')
		from_date2 = datetime.strptime(filters.payroll_year+"-04-01",'%Y-%m-%d')
		to_date2 = datetime.strptime(filters.payroll_year+"-06-30",'%Y-%m-%d')
		from_date3 = datetime.strptime(filters.payroll_year+"-07-01",'%Y-%m-%d')
		to_date3 = datetime.strptime(filters.payroll_year+"-09-30",'%Y-%m-%d')
		from_date4 = datetime.strptime(filters.payroll_year+"-10-01",'%Y-%m-%d')
		to_date4 = datetime.strptime(filters.payroll_year+"-12-31",'%Y-%m-%d')
		result = [{'from_date':from_date1,'to_date':to_date1},{'from_date':from_date2,'to_date':to_date2},{'from_date':from_date3,'to_date':to_date3},{'from_date':from_date4,'to_date':to_date4}]
	return result

def get_year_start_end(filters):
	start_date = datetime.strptime(filters.payroll_year+"-01-01",'%Y-%m-%d')
	end_date = datetime.strptime(filters.payroll_year+"-12-31",'%Y-%m-%d')
	return start_date, end_date
