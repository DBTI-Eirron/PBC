# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

def get_columns(employee_list):
	columns = [
		{
			"fieldname": "HDMF",
			"label": _("Pag-IBIG"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "PHIC",
			"label": _("PhilHealth"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "SSS",
			"label": _("SSS"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "total",
			"label": _("Total"),
			"fieldtype": "Float",
			"width": 120
		},
	]

	return columns

def get_data(filters):
	data = []
	posting_date = ""
	employee_list = get_employees(filters)
	contribution_types = ["HDMF", "PHIC", "SSS"]

	if not employee_list:
		return data

	contribution_map = get_contributions_record(filters)
	if contribution_map:
		for emp in employee_list:
			date = contribution_map.get(emp.name, {}).get(posting_date)
			row = []

			total = 0
			for con in contribution_types:
				contribution_amount = flt(contribution_map.get(emp.name, {}).get(con))
				total += contribution_amount
				row.append(contribution_amount)

			row += [total]

			data.append(row)

	return data

def get_employees(filters):
	cur_user = frappe.session.user
	employees = frappe.db.sql("""SELECT * FROM `tabEmployee` WHERE user_id  = %(user)s """,{ "user": cur_user }, as_dict=True)

	return employees

def get_contributions_record(filters):
	employee_list = get_employees(filters)

	contribution_details = frappe.db.sql(""" SELECT PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent` 
		WHERE employee in (%s) GROUP BY PRE.`name` """ %
		', '.join(['%s']*len(employee_list)), tuple([emp.name for emp in employee_list]), as_dict=1)

	contribution_map = {}
	for d in contribution_details:
		if getdate(filters.from_date) <= getdate(d.posting_date) <= getdate(filters.to_date):
			contribution_map.setdefault(d.employee, frappe._dict()).setdefault(d.pay_code, [])
			if contribution_map[d.employee][d.pay_code]:
				contribution_map[d.employee][d.pay_code] += flt(d.amount, 2)
			else:
				contribution_map[d.employee][d.pay_code] = flt(d.amount, 2)

	return contribution_map