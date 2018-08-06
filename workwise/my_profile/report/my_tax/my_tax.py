# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _, msgprint

def execute(filters=None):
	columns = get_columns(filters)
	data = get_result(filters)

	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "year",
			"label": _("Year"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "month",
			"label": _("Month"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "amount",
			"label": _("Tax"),
			"fieldtype": "Float",
			"width": 120
		},
	]

	return columns

def get_employees(filters):
	employees = frappe.db.sql(""" SELECT `name` FROM tabEmployee WHERE `user_id` = %(employee)s """,{ 
		"employee": frappe.session.user
	}, as_dict=True)

	return employees

def get_result(filters):
	result = []
	employees = get_employees(filters)

	for emp in employees:
		entries = frappe.db.sql("""SELECT
				YEAR(PR.`process_date`) as p_year,
				MONTHNAME(PR.`process_date`) as p_month,
				PR.`process_date`,
				PR.`posting_date`,
				PE.`amount` 
			FROM
				`tabPayroll Register` PR
				JOIN `tabPayroll Register Entries` PE 
			WHERE
				PR.`name` = PE.`parent` 
				AND PE.`pay_code` = "WHTAX"
				AND PR.`employee` = %(employee)s
				AND (PR.`process_date` BETWEEN %(from_date)s AND %(to_date)s)""",{ 
				"employee": emp.name,
				"from_date": filters.from_date,
				"to_date": filters.to_date
		}, as_dict=True)

		total = 0
		for d in entries:
			row = {
				"year": d.p_year,
				"month": d.p_month,
				"date": d.process_date,
				"amount": d.amount
			}

			total += d.amount
			result.append(row)
		result.append(total)

	return result