# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr

def execute(filters=None):
	columns = get_columns(filters)
	data, move_dict = get_data(filters)
	chart = get_chart(filters,move_dict)
	return columns, data, None, chart
def get_data(filters):
	data = []
	move_dict = get_move_dict(filters)
	for move_type in move_dict:
		data.append({"employee":move_type})
		for move in move_dict[move_type]:
			row = move_dict[move_type][move]
			data.append({"employee":"&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"+cstr(row['employee']),"employee_name":row['employee_name'],"company":row['company'],"effective_on":row['effective_on']})
		data.append({})
	return data, move_dict

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"width": 150,
			"options": "Employee"
		},{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 190,
		},{
			"fieldname": "company",
			"label": _("Company"),
			"fieldtype": "Data",
			"width": 200,
		},{
			"fieldname": "effective_on",
			"label": _("Effective Date"),
			"fieldtype": "Data",
			"width": 150,
		}
	]
	return columns

def get_move_dict(filters):
	move_dict = {}
	movement_report = frappe.db.sql("""SELECT name, employee, employee_name, company, movement_type, effective_on, posting_date FROM `tabEmployee Movement` WHERE company = %s AND effective_on BETWEEN %s AND %s""",(filters.company,filters.from_date,filters.to_date),as_dict=True)
	for movement in movement_report:
		if movement.movement_type not in move_dict:
			move_dict.setdefault(movement.movement_type, frappe._dict({movement.name:{}}))
		else:
			move_dict[movement.movement_type][movement.name] = {}
		move_dict[movement.movement_type][movement.name].update({"employee":movement.employee,"employee_name":movement.employee_name,"company":movement.company,"effective_on":movement.effective_on,"movement_type":movement.movement_type})

	return move_dict

def get_chart(filters,move_dict):
	datasets = []
	labels = [move_type for move_type in move_dict]
	values = [len(move_dict[move_type]) for move_type in move_dict]
	datasets.append({'title':'Movement', 'values': values})
	title=filters.company	
	chart = {
		"data": {
			'labels': labels,
			'datasets': datasets
		}
	}
	chart["title"] = title
	chart["type"] = "bar"
	chart["colors"] = ['green', 'blue', 'orange']
	return chart