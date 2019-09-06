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
			"options": "Leave Application",
			"width": 400
		},
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "leave_type",
			"label": _("Leave Type"),
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
		l_app = frappe.db.sql(""" SELECT
			LA.`name`,
			LA.`employee`,
			LA.`full_name`,
			LA.`leave_type`,
			LT.`leave_date`
		FROM
			`tabLeave Application Table` LT
			JOIN `tabLeave Application` LA 
		WHERE
			LT.`parent` = LA.`name` AND LA.`docstatus`= 1 
			AND LA.`employee` = %(employee)s 
			AND LT.`leave_date` >= %(from)s 
			AND LT.`leave_date` <= %(to)s {conditions} """.format(conditions=get_query_conditions(filters)),{ 
				"to": filters.to_date,
				"from": filters.from_date,
				"employee": emp.name,
				"leave_type": filters.leave_type
			}, as_dict=True)

		if l_app:
			data.append({
					"data":"<b>Employee: </b>"+emp.full_name+"",
			})

			data.append({
					"data":"<b>Employee ID: </b>"+emp.name+"",
			})
			
			for app in l_app:
				entry = {
					"date": getdate(app.leave_date),
					"data": app.name,
					"leave_type": app.leave_type
				}
				data.append(entry)

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

	if filters.get("location"):
		conditions.append("`location`=%(location)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 

def get_query_conditions(filters):
	conditions = []
	if filters.leave_type:
		conditions.append("`leave_type`=%(leave_type)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""