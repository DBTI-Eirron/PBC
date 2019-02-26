# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _

def execute(filters=None):

	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "data",
			"label": _("Data"),
			"fieldtype": "Data",
			"width": 600
		},
	]

	return columns

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)
	return result

def get_data(filters):
	#Initialize
	data = []
	company, att_from, att_to = frappe.db.get_value("Payroll Period", filters.payroll_period, ["company", "attendance_from", "attendance_to"])

	data.append({
		"data":"<b>Company: </b>"+filters.company+"",
	})
	data.append({})

	employees = get_employees(filters)
	for emp in employees:
		total_count = 0
		included = 0
		absent_result = frappe.db.sql(""" SELECT `target_date` FROM `tabAttendance Register` WHERE (is_absent != 0 or is_lwop != 0) AND target_date >= %(from)s AND target_date <= %(to)s AND `employee` = %(employee)s ORDER BY `target_date` """,{
			"to": att_to,
			"from": att_from,
			"employee": emp.name,
		}, as_dict=True)

		if absent_result:
			included = 1
		else:
			if included == 0:
				included = 0

		if included == 1:
			data.append({"data":"<b>Employee: </b>"+emp.full_name+"",})
			data.append({"data":"<b>Absent</b>",})

			for absents in absent_result:
				entry = {
					"data": absents.target_date,
				}
				total_count += 1
				data.append(entry)
			
			data.append({"data":"<b>Count: </b>"+str(total_count),})
			data.append({})

	return data

def get_employees(filters):
	register = frappe.db.sql("""SELECT `name`, full_name FROM `tabEmployee` 
		WHERE company = %(company)s {conditions}""".format(conditions=get_conditions(filters)), filters, as_dict=1)

	return register

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 