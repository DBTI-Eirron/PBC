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
			"fieldname": "Employee ID",
			"label": "Employee ID",
			"fieldtype": "Data",
			"width": 90
		},
		{
			"fieldname": "Biometrics ID",
			"label": "Biometrics ID",
			"fieldtype": "Data",
			"width": 90
		},
		{
			"fieldname": "Employee Name",
			"label": "Employee Name",
			"fieldtype": "Data",
			"width": 240
		}
	]
	return columns

def get_data(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql(""" SELECT DISTINCT AR.employee as `xname`, TE.full_name, TE.biometrics_id, (SELECT COUNT(`name`) FROM `tabAttendance Register` WHERE work_hours <> work AND `employee`= xname AND is_restday <> 1 AND is_holiday <> 1 AND target_date >= %(from_date)s AND target_date <= %(to_date)s) AS abs
				FROM `tabAttendance Register` AR INNER JOIN `tabEmployee` TE ON AR.employee = TE.`name` 
				WHERE TE.company = %(company)s 
				AND (AR.target_date BETWEEN %(from_date)s AND %(to_date)s)
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s) 
				ORDER BY AR.employee
				""",{ 
				"company": filters.company,
				"from_date": filters.from_date,
				"to_date": filters.to_date,
				"user": frappe.session.user
			}, as_dict=True)
	else:
		employees = frappe.db.sql("""SELECT DISTINCT AR.employee as `xname`, TE.full_name, TE.biometrics_id, (SELECT COUNT(`name`) FROM `tabAttendance Register` WHERE work_hours <> work AND `employee`= xname AND is_restday <> 1 AND is_holiday <> 1 AND target_date >= %(from_date)s AND target_date <= %(to_date)s) AS abs
				FROM `tabAttendance Register` AR INNER JOIN `tabEmployee` TE ON AR.employee = TE.`name` 
				WHERE TE.company = %(company)s 
				AND (AR.target_date BETWEEN %(from_date)s AND %(to_date)s)
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
				ORDER BY AR.employee
				""",{ 
				"company": filters.company,
				"from_date": getdate(filters.from_date),
				"to_date": getdate(filters.to_date)
			}, as_dict=True)
		
	data = format_entries(filters,employees)
	return data

def format_entries(filters,entries):
	data = []
	for ent in entries:
		if ent.abs is None or ent.abs == 0:
			da = {
			"Employee ID":ent.xname,
			"Biometrics ID":ent.biometrics_id,
			"Employee Name":ent.full_name
			}
			data.append(da)
	return data
	


