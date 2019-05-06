# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_columns(employee_list):
	columns = [
		{
			"fieldname": "description_1",
			"label": _("Earnings"),
			"fieldtype": "Data",
			"width": 250
		},
		{
			"fieldname": "amount_1",
			"label": _(""),
			"fieldtype": "Data",
			"width": 250
		},
		{
			"fieldname": "description_2",
			"label": _("Deduction"),
			"fieldtype": "Data",
			"width": 250
		},
		{
			"fieldname": "amount_2",
			"label": _(""),
			"fieldtype": "Data",
			"width": 250
		},
	]

	return columns

def get_data(filters):
	data = []

	data.append(
		{
			"description_1": "Description",
			"amount_1": "Amount",
			"description_2": "Description",
			"amount_2": "Amount",
		}
	)

	return data