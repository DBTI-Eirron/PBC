# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import getdate
from frappe.utils import flt
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
			"width": 400
		},
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "total_hours",
			"label": _("Total Hours"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "tags",
			"label": _("Tags"),
			"fieldtype": "Data",
			"width": 400
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

def get_overtime_map():
	ot_map = {}
	ot = frappe.db.sql(""" SELECT ot_name, ot_code, ot_rate FROM `tabOvertime Rates` """, as_dict=1)
	for t in ot:
		ot_map[t.ot_code] = {
			"name": t.ot_name
		}
	return ot_map

def init_map(filters):
	init_data = frappe.db.sql("""SELECT `name`, full_name, employee_id FROM `tabEmployee` PR
		WHERE company = %(company)s {conditions} """.format(conditions=get_conditions_emp(filters)), filters, as_dict=1)

	_map = frappe._dict()
	for d in init_data:
		_map.setdefault(d.name, frappe._dict({
				"employee": d.name,
				"employee_name": d.full_name,
				"employee_id": d.employee_id,
				"registers": [],
				"overtimes": [],
				"overtime_apps": [],
			})
		)

	return _map

def get_overtimes(_map, filters):
	overtimes = frappe.db.sql("""SELECT * FROM `tabOvertime` WHERE target_date >= %(from_date)s 
		AND target_date <= %(to_date)s {conditions} """.format(conditions=get_conditions(filters)), filters, as_dict=1)

	for d in overtimes:
		if d.employee in _map:
			_map[d.employee].overtimes.append(d)

def get_overtime_apps(_map, filters):
	overtime_apps = frappe.db.sql("""SELECT `name`, `employee`, target_date FROM `tabOvertime Application` 
		WHERE workflow_state = 'Approved' AND target_date >= %(from_date)s AND target_date <= %(to_date)s {conditions} """.format(conditions=get_conditions(filters)), filters, as_dict=1)

	for d in overtime_apps:
		if d.employee in _map:
			_map[d.employee].overtime_apps.append(d)

def get_registers(_map, filters):
	registers = frappe.db.sql("""SELECT employee, target_date, overtime, overtime_nd, overtime_ex FROM `tabAttendance Register` 
		WHERE target_date >= %(from_date)s AND target_date <= %(to_date)s ORDER BY target_date ASC """.format(conditions=get_conditions(filters)), filters, as_dict=1)

	for d in registers:
		if d.employee in _map:
			_map[d.employee].registers.append(d)

def get_conditions_emp(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")

	if filters.get("period_group"):
		conditions.append("`period_group`='{0}'".format(filters.get("period_group")))

	return "and {}".format(" and ".join(conditions)) if conditions else "" 

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`employee`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 

def get_data(filters):
	data = []	
	_map = init_map(filters)
	ot_map = get_overtime_map()
	get_overtimes(_map, filters)
	get_overtime_apps(_map, filters)
	get_registers(_map, filters)

	for e, edict in sorted(_map.items(), key=lambda x: x[1]['employee_name']):
		if edict['overtimes']:
			data.append({"data":"<b>Employee: </b>"+edict.employee_name+"",})
			data.append({"data":"<b>Employee ID: </b>"+edict.employee_id+"",})
			total_ot_hrs = 0.0
			for reg in edict['registers']:
				entry = {
					"data": "",
					"date": reg.target_date,
					"total_hours": 0.0,
					"tags": "",
				}
				for ota in edict['overtime_apps']:
					if getdate(reg.target_date) == getdate(ota.target_date):
						if entry['data']:
							entry['data'] += ", "+ota.name+""
						else:
							entry['data'] += ota.name

				for ot in edict['overtimes']:
					if getdate(reg.target_date) == getdate(ot.target_date):
						entry['total_hours'] += ot.hrs
						entry['tags'] += "<span class='label label-success'>"+ot_map[ot.ot_code]['name']+""+str(flt(ot.hrs, 2))+" Hrs </span>"

				if entry['total_hours'] > 0:
					total_ot_hrs += entry['total_hours']
					data.append(entry)

			data.append({
				"data":"<b>Total</b>",
				"total_hours": flt(total_ot_hrs, 2)
			})
			data.append({})
				
	return data
 