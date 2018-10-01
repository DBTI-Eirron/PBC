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
	from_date = getdate(filters.from_date)
	to_date = getdate(filters.to_date)
	entries = frappe.db.sql("""SELECT name AS xname, biometrics_id, full_name, (SELECT sum(`is_absent`) FROM `tabAttendance Register` WHERE `employee`= xname AND target_date >= %s AND target_date <= %s) AS abs FROM `tabEmployee` WHERE `company` = %s""",(from_date,to_date,filters.company),as_dict=True)
	data = format_entries(filters,entries)
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
	


