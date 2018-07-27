# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import getdate
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
			"fieldtype": "Link",
			"options": "Overtime Application",
			"width": 400
		},
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "total_hours",
			"label": _("Total Hours"),
			"fieldtype": "Data",
			"width": 120
		}
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

	data.append({
		"data":"<b>Company: </b>"+filters.company+"",
	})
	data.append({})

	employees = get_employees(filters)
	for emp in employees:
		ot_app = frappe.db.sql(""" SELECT `name`, `employee`, `full_name`, `target_date`, `total_hrs` FROM `tabOvertime Application` WHERE `docstatus` = 1 AND `employee` = %(employee)s AND `target_date` >= %(from)s AND `target_date` <= %(to)s """,{
			"to": filters.to_date,
			"from": filters.from_date,
			"employee": emp.name,
		}, as_dict=True)

		if ot_app:
			data.append({
					"data":"<b>Employee: </b>"+emp.full_name+"",
			})

			data.append({
					"data":"<b>Employee ID: </b>"+emp.name+"",
			})
			
			total_ob_hrs = 0.0
			for app in ot_app:
				
				entry = {
					"date": getdate(app.target_date),
					"data": app.name,
					"total_hours": app.total_hrs
				}
				total_ob_hrs += flt(app.total_hrs)
				data.append(entry)

			data.append({
				"data":"<b>Total</b>",
				"total_hours": total_ob_hrs
			})
			data.append({})

	return data

def convert_secs(filters, secs):
	con = 0
	if filters.time_options == "Mins":
		con = flt(secs, 8) * 60
	else:
		con = flt(secs, 8)
	return flt(con, 8)

def get_employees(filters):
	register = frappe.db.sql("""SELECT `name`, full_name FROM `tabEmployee` 
		WHERE company = %(company)s {conditions}""".format(conditions=get_conditions(filters)), filters, as_dict=1)

	return register

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 