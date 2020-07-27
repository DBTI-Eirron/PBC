# Copyright (c) 2013, Opensoft Solutions Inc.
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import date
from frappe import _
from frappe.utils import getdate, cstr, flt

def execute(filters=None):
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "leave_type",
			"label": _("Leave Type"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "leave_id",
			"label": _("Leave ID"),
			"fieldtype": "Link",
			"options": "Leave Application",
			"width": 100
		},
		{
			"fieldname": "leave_date",
			"label": _("Leave Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "leave_days",
			"label": _("Leave Days"),
			"fieldtype": "float",
			"width": 120
		},
		{
			"fieldname": "reason",
			"label": _("Reason"),
			"fieldtype": "Data",
			"width": 120
		},
	]

	return columns

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_emp_map(filters):
	init_data = frappe.db.sql(""" SELECT `name`, full_name FROM tabEmployee WHERE `company` = %(company)s
		AND is_active = 1 {conditions} """.format(conditions=get_conditions(filters)), filters, as_dict=1)

	_map = frappe._dict()
	for d in init_data:
		_map.setdefault(d.name, frappe._dict({
				"employee": d.name,
				"employee_name": d.full_name,
				"leaves": []
			})
		)

	return _map
					
def get_data(filters):
	data = []
	emp_map = get_emp_map(filters)

	leaves = frappe.db.sql("""SELECT LA.`name`, LA.employee, LA.full_name, LAT.leave_date, LA.leave_type, LAT.is_half_day, LAT.is_excluded, LA.remarks 
		FROM `tabLeave Application` LA 
		INNER JOIN `tabLeave Application Table` LAT ON LAT.parent = LA.`name`
		WHERE company = %(company)s 
		AND LAT.leave_date >= %(from_date)s 
		AND LAT.leave_date <= %(to_date)s
		AND LA.convert_cash = 1 AND LA.docstatus = 1 AND LAT.is_excluded != 1 {conditions}""".format(conditions=get_lv_conditions(filters)), filters, as_dict=1)

	#Insert to dict Leaves per Employee
	for ll in leaves:
		if ll.employee in emp_map:
			emp_map[ll.employee].leaves.append(ll)

	#Total Leaves per employee
	if filters.location:
		data.append({
			"leave_type":  "<b>"+cstr(filters.location)+"</b>",
		})
		data.append({})

	for e, edict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
		entry = []
		entry.append({
			"leave_type":  "<b>"+cstr(edict['employee_name'])+"</b>",
		})

		total_leave_days = 0
		for lv in edict['leaves']:
			if lv.is_half_day:
				leave_days = 0.5
				total_leave_days += 0.5
			else:
				leave_days = 1.0
				total_leave_days += 1.0

			entry.append({
				"leave_type": lv.leave_type,
				"leave_id": lv.name,
				"leave_date":  lv.leave_date,
				"leave_days": leave_days,
				"reason": lv.remarks,
			})

		entry.append({
			"leave_type":  "<b>TOTAL</b>",
			"leave_days":  total_leave_days,
		})
		entry.append({})		
		if total_leave_days > 0:
			data.extend(entry)
				
	return data
 
def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")

	if filters.get("location"):
		conditions.append("location=%(location)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_lv_conditions(filters):
	conditions = []

	if filters.get("leave_type"):
		conditions.append("leave_type=%(leave_type)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)

	return result
 