# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	results = get_result(filters)
	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "net_payroll",
			"label": _("Net Payroll"),
			"fieldtype": "'Data'",
			"width": 120
		},	
	]

	return columns

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_data(filters):
	data = []
	total_payroll = 0.0

	totals = {
		"net_payroll": 0,
		"employee": "<b>TOTAL</b>",
		"employee_name": "",
	}

	if not "Administrator" in frappe.get_roles(frappe.session.user):
		register = frappe.db.sql(""" SELECT PR.employee, PR.employee_name, PR.net_payroll, E.cost_center
			FROM `tabPayroll Register` PR 
			INNER JOIN tabEmployee E ON E.`name` = PR.employee WHERE 
			E.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s)
			AND E.cost_center = %s AND PR.period = %s """, (frappe.session.user, filters.cost_center, filters.period), as_dict=1)
	else:
		register = frappe.db.sql(""" SELECT PR.employee, PR.employee_name, PR.net_payroll, E.cost_center
			FROM `tabPayroll Register` PR 
			INNER JOIN tabEmployee E ON E.`name` = PR.employee WHERE 
			E.cost_center = %s AND PR.period = %s """, (filters.cost_center, filters.period), as_dict=1)

	for d in register:
		data.append(d)
		total_payroll += d.net_payroll

	totals['net_payroll'] = total_payroll
	data.append(totals)

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = {
			"employee": d.get("employee"),
			"employee_name": d.get("employee_name"),
			"net_payroll": format_precision(d.get("net_payroll"), filters.value_precision),
		}
		result.append(row)
	return result