# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	employee_list = get_employees(filters)
	
	if not employee_list:
		frappe.throw(_("No record found"))
		return columns, employee_list

	data = []

	for emp in employee_list:
		row = ["", emp.employee_name, emp.training, emp.provider, "", "", emp.schedule, "", emp.budget]

		data.append(row)

	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "department",
			"label": _("SUBSIDIARY/DEAPRTMENT"),
			"fieldtype": "Data",
			"width": 160
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "training",
			"label": _("TITLE OF SEMINAR/TRAINING"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "provider",
			"label": _("TRAINING PROVIDER"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "contact",
			"label": _("CONTACT NUMBER/EMAIL ADD"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "lrf_date",
			"label": _("DATE LRF RECEIVED"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "reg_date",
			"label": _("DATE REGISTERED"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "amount",
			"label": _("ACTUAL AMOUNT"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "paid",
			"label": _("AMOUNT PAID"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "savings",
			"label": _("SAVINGS"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "date_attended",
			"label": _("DATE ATTENDED"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "sac_due",
			"label": _("SAC DUE"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "sac_date_submitted",
			"label": _("DATE SAC SUBMITTED"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "application_plan",
			"label": _("PLAN OF APPLICATION"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "application_status",
			"label": _("STATUS OF APPLICATION"),
			"fieldtype": "Data",
			"width": 180
		},
	]

	return columns

def get_employees(filters):
	employees = frappe.db.sql(""" SELECT DISTINCT
		employee_name,
		training,
		provider,
		`schedule`,
		budget
	FROM
		`tabWLD Needs Table` 
	WHERE
		`parent` = %s AND docstatus = 1 """, (filters.wld_needs), as_dict=True)

	return employees