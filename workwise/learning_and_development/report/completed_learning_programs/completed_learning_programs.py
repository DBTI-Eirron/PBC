# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, ast
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	data = []
	data_entry = {}

	wld_list = frappe.db.sql(""" SELECT WT.`training`, WT.`parent`, WT.`employee`, WT.`employee_name` 
		FROM `tabWLD Needs Table` WT INNER JOIN `tabWLD Needs` WN ON WT.`parent` = WN.`name`
		WHERE WT.`status` = "Completed" AND WN.`docstatus` = 1 AND WN.`company` = %(company)s {conditions} """.format(conditions=get_employee_conditions(filters)),{ 
		"company": filters.company,
		"employee": filters.employee,
	}, as_dict=True)

	for wld in wld_list:
		if wld.employee not in data_entry:
			data_entry[wld.employee] = {
				"programs": [],
				"employee_name": wld.employee_name
			}
		data_entry[wld.employee]['programs'].append(wld.training)

	event_list = frappe.db.sql(""" SELECT LP.`parent`, LP.`employee`, LP.`employee_name`, LP.`company`, LP.`attendance_data`
		FROM `tabLearning Participants` LP INNER JOIN `tabLearning Event` LE ON LP.`parent` = LE.`name`
		WHERE LP.`docstatus` = 1 AND LP.`company` = %(company)s {conditions} """.format(conditions=get_employee_conditions(filters)),{ 
		"company": filters.company,
		"employee": filters.employee,
	}, as_dict=True)

	for eve in event_list:
		if eve.attendance_data:
			attn_data = ast.literal_eval(eve.attendance_data)
			for ses in attn_data:
				if attn_data[ses] == "Present":
					if eve.employee not in data_entry:
						data_entry[eve.employee] = {
							"programs": [],
							"employee_name": eve.employee_name
						}
					if ses not in data_entry[eve.employee]['programs']:
						data_entry[eve.employee]['programs'].append(cstr(ses))

	if data_entry and (not filters.employee):
		for dat in data_entry:
			row = {
				"program": "<b>"+cstr(data_entry[dat]['employee_name'])+"</b>"
			}
			data.append(row)
			for prog in data_entry[dat]['programs']:
				row = {
					"program": cstr(prog),
				}
				data.append(row)

	if data_entry and filters.employee:
		for dat in data_entry:
			if cstr(filters.employee) == dat:
				row = {
					"program": "<b>"+cstr(data_entry[dat]['employee_name'])+"</b>"
				}
				data.append(row)
				for prog in data_entry[dat]['programs']:
					row = {
						"program": cstr(prog),
					}
					data.append(row)

	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "program",
			"label": _("Learning Program"),
			"fieldtype": "Data",
			"width": 600
		},
	]

	return columns

	

def get_employee_conditions(filters):
	conditions = []
	if filters.employee:
		conditions.append("`employee`=%(employee)s")

	return "AND {}".format(" AND ".join(conditions)) if conditions else ""