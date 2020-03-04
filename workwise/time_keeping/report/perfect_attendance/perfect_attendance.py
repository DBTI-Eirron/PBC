# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):

	columns = [
		{
			"fieldname": "employee",
			"label": "Employee ID",
			"fieldtype": "Data",
			"width": 90
		},
		{
			"fieldname": "biometrics_id",
			"label": "Biometrics ID",
			"fieldtype": "Data",
			"width": 90
		},
		{
			"fieldname": "full_name",
			"label": "Employee Name",
			"fieldtype": "Data",
			"width": 240
		}
	]
	return columns

def get_data(filters):
	data = []
	included_list = []
	remove_list = []	
	employees = frappe.db.sql(""" SELECT AR.employee, TE.`biometrics_id`, TE.`full_name`, AR.is_holiday, AR.is_restday, AR.is_absent, AR.is_lwop, AR.late, AR.undertime, AR.cto, AR.work, AR.lv_status, AR.work_hours
		FROM `tabAttendance Register` AR INNER JOIN `tabEmployee` TE ON AR.employee = TE.`name` 
		WHERE TE.company = %(company)s 
		AND (AR.target_date BETWEEN %(from_date)s AND %(to_date)s)
		ORDER BY TE.full_name """,{ 
		"company": filters.company,
		"from_date": filters.from_date,
		"to_date": filters.to_date,
	}, as_dict=True)

	for emp in employees:
		row = {
			"employee": emp.employee,
			"biometrics_id": emp.biometrics_id,
			"full_name": emp.full_name,
		}
		if emp.is_holiday != 1 and emp.is_restday != 1:
			work = 0
			work += emp.cto
			work += emp.work

			if work >= emp.work_hours:
				if row not in data:
					data.append(row)
			if work < emp.work_hours:
				if row in data:
					data.remove(row)

	return data