# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr
from frappe import _

def execute(filters=None):

	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "data",
			"label": _("Data"),
			"fieldtype": "Data",
			"width": 600
		},
	]

	return columns

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)
	return result

def get_data(filters):
	#Initialize
	data = []
	data_entry = {}
	company = frappe.db.get_value("Payroll Period", filters.payroll_period, ["company"])
	att_to = getdate(filters.from_date)
	att_from = getdate(filters.to_date)

	data.append({	"data":"Company: "+filters.company+"",	})
	data.append({})

	employees = get_employees(filters, att_to, att_from)
	for emp in employees:
		if emp.employee not in data_entry:
			data_entry[emp.employee] = {
				"employee_id": cstr(emp.employee),
				"employee_name": cstr(emp.full_name),
				"absents": [],
				"absent_count": 0,
			}

		tags = ""
		if emp.is_halfday:
			tags = "<span class='label label-danger'> Halfday </span>"

		data_entry[emp.employee]['absents'].append( str(getdate(emp.target_date))+" "+tags )
		data_entry[emp.employee]['absent_count'] += 1

	for dat in data_entry:
		data.append({"data":"Employee: "+cstr(data_entry[dat]['employee_name'])+"",})
		data.append({"data":"Absent",})
		for ab in sorted(data_entry[dat]['absents']):
			data.append( {"data": str(ab) })
		data.append({"data":"Count: "+str(data_entry[dat]['absent_count']),})
		data.append({})

	return data

def get_employees(filters, att_to, att_from):
	register = frappe.db.sql(""" SELECT AR.`target_date`, TE.`full_name`, AR.`employee`, AR.`is_halfday` FROM `tabAttendance Register` AR 
		INNER JOIN `tabEmployee` TE ON AR.`employee` = TE.`name`
		LEFT JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name`
		WHERE TE.`is_attendance_base` = 1 AND (AR.is_absent > 0 OR AR.is_lwop > 0) AND AR.target_date >= %(date_to)s AND AR.target_date <= %(date_from)s 
		{conditions} GROUP BY AR.`name` ORDER BY AR.`target_date` """.format(conditions=get_conditions(filters)),{
		"date_to": getdate(att_to),
		"date_from": getdate(att_from),
	}, as_dict=True)
	
	return register

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("AR.`employee`='{0}'".format(filters.employee))

	if filters.get("department"):
		lft, rgt = frappe.db.get_value("Department", filters.department, ["lft", "rgt"])
		conditions.append(_("( DEPT.`lft` BETWEEN '{0}' AND '{1}' )").format(lft, rgt))

	if filters.get("company"):
		conditions.append("TE.`company`='{0}'".format(filters.company))

	if filters.get("show_active"):
		conditions.append("TE.is_active=1")

	if filters.get("period_group"):
		conditions.append("TE.`period_group`='{0}'".format(filters.get("period_group")))

	return "AND {}".format(" AND ".join(conditions)) if conditions else ""