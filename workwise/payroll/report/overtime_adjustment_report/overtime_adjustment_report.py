# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from datetime import timedelta
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_result(filters):
	results = []
	employees_data = {}
	query_filters = {'company': filters.company, 'previous_payroll_period': filters.previous_payroll_period, 'current_payroll_period': filters.current_payroll_period}

	if filters.employee:
		query_filters['employee'] = filters.employee

	if filters.date:
		query_filters['target_date'] = filters.date

	if filters.type_of_overtime:
		query_filters['ot_code'] = frappe.db.get_value("Overtime Rates", filters.type_of_overtime, "ot_code")

	oar_list = frappe.get_all("Overtime Adjustment Register", filters=query_filters, fields=['*'])
	for oar in oar_list:
		if oar.employee not in employees_data:
			department, branch, position_title = frappe.db.get_value("Employee", oar.employee, ["department", "branch", "position_title"])
			employees_data[oar.employee] = {
				"ot_list": [],
				"department": department,
				"branch": branch,
				"position_title": position_title,
			}
		employees_data[oar.employee]["ot_list"].append(oar)

	data_filters = []
	if filters.branch:
		data_filters.append('x["branch"] == {}'.format(filters.branch))

	if filters.department:
		data_filters.append('x["department"] == {}'.format(filters.department))

	if filters.position_title:
		data_filters.append('x["position_title"] == {}'.format(filters.position_title))

	if data_filters:
		data_filters = ' and '.join(data_filters)
		employees_data = filter(lambda x: eval(data_filters), employees_data.values())

	for edata in employees_data:
		for ot in employees_data[edata]['ot_list']:
			result_row = {
				"employee": ot.get('employee'),
				"employee_name": ot.get('employee_name'),
				"date": ot.get('target_date'),
				"branch": employees_data[edata].get('branch'),
				"department": employees_data[edata].get('department'),
				"position_title": employees_data[edata].get('position_title'),
				"type_of_overtime": ot.get('ot_code'),
				"no_of_hours": ot.get('hrs'),
				"amount": ot.get('amount'),
				"remarks": ot.get('remarks')
			}
			results.append(result_row)
	
	return results

def get_columns(filters):
	return [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "employee_name",
			"label": _("Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "branch",
			"label": _("Branch"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "department",
			"label": _("Department"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "position_title",
			"label": _("Position Title"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "type_of_overtime",
			"label": _("Type of Overtime"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "no_of_hours",
			"label": _("No. of Hours"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "remarks",
			"label": _("Remarks"),
			"fieldtype": "Data",
			"width": 150
		}
	]