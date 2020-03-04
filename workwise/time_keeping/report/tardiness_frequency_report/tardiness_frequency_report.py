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
			"width": 400
		},
		{
			"fieldname": "time",
			"label": _("Count"),
			"fieldtype": "Int",
			"width": 120
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
	company, att_from, att_to =  filters.company, filters.from_date, filters.to_date

	data.append({
		"data":"Company: "+filters.company+"",
	})
	data.append({})

	employees = get_employees(filters)
	for emp in employees:
		included = 0

		late_result = frappe.db.sql(""" SELECT `target_date`,`late` FROM `tabAttendance Register` WHERE late != 0 AND target_date >= %(from)s AND target_date <= %(to)s AND `employee` = %(employee)s ORDER BY `target_date` """,{
				"to": att_to,
				"from": att_from,
				"employee": emp.name,
		}, as_dict=True)

		if late_result:
			included = 1
		else:
			if included == 0:
				included = 0

		undertime_result = frappe.db.sql(""" SELECT `target_date`, `undertime` FROM `tabAttendance Register` WHERE undertime != 0 AND target_date >= %(from)s AND target_date <= %(to)s AND `employee` = %(employee)s ORDER BY `target_date` """,{
			"to": att_to,
			"from": att_from,
			"employee": emp.name,
		}, as_dict=True)

		if undertime_result:
			included = 1
		else:
			if included == 0:
				included = 0

		if included == 1:
			data.append({"data":"Employee: "+emp.full_name+"",})
			
			total_late = 0
			for lates in late_result:
				total_late += 1
			total_late_data = {
				"data": _("Late"),
				"time": total_late
			}
			data.append(total_late_data)

			total_undertime = 0
			for undertimes in undertime_result:
				total_undertime += 1
			total_undertime_data = {
				"data": _("Undertime"),
				"time": total_undertime
			}
			data.append(total_undertime_data)
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