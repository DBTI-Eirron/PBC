# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, today

def execute(filters=None):
	columns = get_columns(filters)
	data = get_result(filters)
	return columns, data

def get_columns(filters):
	if filters.department:
		label = "Employee"
	else:
		label = "Department"
	columns = [{
		"fieldname":"name",
		"label": _(label),
		"fieldtype": "Data",
		"width": 160
	}]
	period = frappe.db.sql("""SELECT `name` FROM `tabPayroll Year`""",as_dict=True)
	for per in period:
		columns += [{
			"fieldname": per.name,
			"label": _(per.name),
			"fieldtype": "Data",
			"width": 160
		}]
	return columns

def get_result(filters):
	result = []
	additional_filter = add_filter(filters)
	department = frappe.db.sql("""SELECT `name` FROM `tabDepartment` """+additional_filter,as_dict=True)
	if filters.department:
		period = frappe.db.sql("""SELECT `name`,to_date,from_date FROM `tabPayroll Year`""",as_dict=True)
		all_employee = []
		for per in period:
			employees = frappe.db.sql_list("""SELECT DISTINCT appraisee as xappraisee FROM `tabEvaluation` WHERE department = %s AND company = %s AND from_date BETWEEN %s AND %s""",(filters.department,filters.company,per.from_date,per.to_date))
			all_employee = list(set(all_employee+employees))
		for emp in all_employee:
			row = {"name":emp}
			for per in period:
				total_score = frappe.db.sql_list("""SELECT SUM(total_score) FROM `tabEvaluation` WHERE department = %s AND company = %s AND from_date BETWEEN %s AND %s""",(filters.department,filters.company,per.from_date,per.to_date))
				row.update({per.name:total_score[0]})
			result.append(row)
	else:
		for dep in department:
			row = {}
			row.update({"name":dep.name})
			period = frappe.db.sql("""SELECT `name`,to_date,from_date FROM `tabPayroll Year`""",as_dict=True)
			for per in period:
				total_score =  frappe.db.sql("""SELECT AVG(total_score) as score FROM `tabEvaluation` WHERE department = %s AND company = %s AND from_date BETWEEN %s AND %s""",(dep.name,filters.company,per.from_date,per.to_date),as_dict=True)
				row.update({per.name:'{:.2f}'.format(flt(total_score[0]['score']))})
			result.append(row)
	return result


def add_filter(filters):
	additional_filter = ""
	if filters.department:
		additional_filter += "WHERE `name`= '"+filters.department+"'"

	return additional_filter