# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "target_date",
			"label": _("Data"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "work",
			"label": _("Work"),
			"fieldtype": "Float",
			"width": 60
		},
#		{
#			"fieldname": "break",
#			"label": _("Break"),
#			"fieldtype": "Float",
#			"width": 60
#		},		
		{
			"fieldname": "late",
			"label": _("Late"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "overtime",
			"label": _("OT"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "overtime_nd",
			"label": _("OT ND"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "overtime_ex",
			"label": _("OT EX"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "nightdiff",
			"label": _("ND"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "cto",
			"label": _("CTO"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "undertime",
			"label": _("UT"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "tags",
			"label": _("Tags"),
			"fieldtype": "Data",
			"width": 400
		},
		{
			"fieldname": "links",
			"label": _("Links"),
			"fieldtype": "Data",
			"width": 400
		},
	]

	if filters.flt_precision:
		precision_fields = ["work","break","late","overtime","overtime_nd","overtime_ex","nightdiff","cto","undertime"]
		for d in columns:
			if d.get('fieldname') in precision_fields:
				d['precision'] = cint(filters.flt_precision)

	return columns

def get_data(filters):
	data = []
	register_filters = {
		"company": filters.get("company"),
		"payroll_period": filters.get("previous_payroll_period"),
		"target_period": filters.get("current_payroll_period")
	}

	employees = get_employees(filters)
	if employees:
		data.append({
		"target_date":"<b>Company: </b>"+filters.company+"",
		})
		if filters.department:
			data.append({
				"target_date":"<b>Department: </b>"+filters.department+"</b>",
			})
		if filters.location:
			data.append({
				"target_date":"<b>Location: </b>"+filters.location+"</b>",
			})
		data.append({
			"target_date":"<b>Period: </b>"+cstr(filters.previous_payroll_period)+"</b>",
		})
		data.append({
			"target_date":"<b>Target Period: </b>"+cstr(filters.current_payroll_period)+"</b>",
		})
		data.append({})

	for emp in employees:
		register_filters["employee"] = emp['employee']
		adjusted_registers = frappe.get_all("Adjustment Register Adjusted", filters=register_filters, fields=["*"], order_by="date")
		has_adjustment = 0
		datarow = []
		for adjusted in adjusted_registers:
			processed_registers_filters = register_filters
			processed_registers_filters['date'] = adjusted.get("date")
			processed_registers = frappe.get_all("Adjustment Register Processed", filters=processed_registers_filters, fields=["*"])
			#Check if has difference
			has_diff = 0
			if processed_registers:
				if processed_registers[0].get("worked_hours") != adjusted.get("worked_hours"):
					has_diff = 1
				if processed_registers[0].get("break") != adjusted.get("break"):
					has_diff = 1
				if processed_registers[0].get("late_hours") != adjusted.get("late_hours"):
					has_diff = 1
				if processed_registers[0].get("overtime_hours") != adjusted.get("overtime_hours"):
					has_diff = 1
				if processed_registers[0].get("overtime_nd_hours") != adjusted.get("overtime_nd_hours"):
					has_diff = 1
				if processed_registers[0].get("overtime_ex_hours") != adjusted.get("overtime_ex_hours"):
					has_diff = 1
				if processed_registers[0].get("night_difference_hours") != adjusted.get("night_difference_hours"):
					has_diff = 1
				if processed_registers[0].get("cto") != adjusted.get("cto"):
					has_diff = 1
				if processed_registers[0].get("undertime_hrs") != adjusted.get("undertime_hrs"):
					has_diff = 1
				if processed_registers[0].get("tags") != adjusted.get("tags"):
					has_diff = 1
				if processed_registers[0].get("links") != adjusted.get("links"):
					has_diff = 1
			else:
				has_diff = 1

			if has_diff:
				has_adjustment = 1
				row = {
					"target_date": adjusted.get("date"),
					"work": adjusted.get("worked_hours"),
					"break": adjusted.get("break"),
					"late": adjusted.get("late_hours"),
					"overtime": adjusted.get("overtime_hours"),
					"overtime_nd": adjusted.get("overtime_nd_hours"),
					"overtime_ex": adjusted.get("overtime_ex_hours"),
					"nightdiff": adjusted.get("night_difference_hours"),
					"cto": adjusted.get("cto"),
					"undertime": adjusted.get("undertime_hrs"),
					"tags": adjusted.get("tags"),
					"links": adjusted.get("links"),
				}
				datarow.append(row)
		if has_adjustment:
			data.append({"target_date":"<b>"+emp['employee_name']+"</b>"})
			data.extend(datarow)
			data.append({})

	return data

def get_employees(filters):
	conditions = ""
	if filters.get("employee"):
		conditions += " AND AR.employee = '{0}' ".format(filters.get("employee"))

	if filters.get("department"):
		conditions += " AND TE.department = '{0}' ".format(filters.get("department"))

	if filters.get("location"):
		conditions += " AND TE.location = '{0}' ".format(filters.get("location"))

	if filters.get("position_title"):
		conditions += " AND TE.position_title = '{0}' ".format(filters.get("position_title"))

	if filters.get("show_active"):
		conditions += " AND TE.is_active = 1 "

	employees = frappe.db.sql("""SELECT DISTINCT AR.employee, AR.employee_name FROM `tabAdjustment Register Adjusted` AR 
		INNER JOIN `tabEmployee` TE ON AR.employee=TE.`name`
		WHERE AR.company = %s AND AR.payroll_period = %s 
		AND AR.target_period = %s {conditions} ORDER BY AR.employee_name """.format(conditions=conditions),(
		filters.get("company"), 
		filters.get("previous_payroll_period"), 
		filters.get("current_payroll_period")
	), as_dict=1)

	return employees