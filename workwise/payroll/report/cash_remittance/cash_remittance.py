# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters, columns)
	data = get_data(filters, data)

	return columns, data

def get_columns(filters, columns):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 160
		},
		{
			"fieldname": "full_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 260
		},
		{
			"fieldname": "net_payroll",
			"label": _("Netpay"),
			"fieldtype": "Float",
			"width": 160
		}
	]

	return columns

def get_data(filters, data):
	data = frappe.db.sql(""" SELECT PR.`employee`, TE.`full_name`, PR.`net_payroll` 
		FROM `tabPayroll Register` PR LEFT JOIN `tabEmployee` TE ON PR.`employee`=TE.`name`
		WHERE PR.`period`=%(payroll_period)s AND TE.`company`=%(company)s AND TE.`mode_of_payment`='Cash' ORDER BY TE.`full_name` """,filters, as_dict=1)

	return data