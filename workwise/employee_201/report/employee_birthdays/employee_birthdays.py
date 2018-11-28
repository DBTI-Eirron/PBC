# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, dateutil
from datetime import date  
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_columns(filters):

	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100
		},
		{
			"fieldname": "full_name",
			"label": _("Full Name"),
			"fieldtype": "Data",
			"width": 240
		},
		{
			"fieldname": "birthday",
			"label": _("Birthday"),
			"fieldtype": "Date",
			"width": 180
		},
	]

	return columns

def get_data(filters):
	employees = frappe.db.sql("""SELECT `name` as employee, full_name, birthday
		FROM tabEmployee
		WHERE company = %(company)s
		AND is_active = 1 ORDER BY last_name, first_name""",{ 
			"company": filters.company
		}, as_dict=True)

	return employees