# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters, columns)
	data = get_data(filters, data)
	
	if not data:
		frappe.throw(_("No record found"))
		return columns, data

	return columns, data

def get_columns(filters, columns):
	columns = [
		{
			"fieldname": "session",
			"label": _("Session"),
			"fieldtype": "Data",
			"width": 400
		},
		{
			"fieldname": "average_rating",
			"label": _("Average Rating"),
			"fieldtype": "Data",
			"width": 160
		},
		{
			"fieldname": "evaluators",
			"label": _("Evaluators"),
			"fieldtype": "data",
			"width": 160
		},
	]

	return columns

def get_data(filters, data):
	data_entry = {}
	evaluation_list = frappe.db.sql(""" SELECT `learning_session`, average_rating FROM `tabLearning Session Evaluation` 
		WHERE learning_event = %s  AND docstatus = 1 AND `company` = %s GROUP BY `name` """, (filters.event, filters.company), as_dict=True)
	
	for s in evaluation_list:
		if s.learning_session not in data_entry:
			data_entry[s.learning_session] = {
				"average_rating": 0.00,
				"evaluators": 0,
			}

		data_entry[s.learning_session]['average_rating'] += flt(s.average_rating, 2)
		data_entry[s.learning_session]['evaluators'] += 1

	for dat in data_entry:
		if data_entry[dat]['evaluators'] > 1:
			data_entry[dat]['average_rating'] = flt(data_entry[dat]["average_rating"], 2) / flt(data_entry[dat]["evaluators"], 2)

		row = {
			"session" : dat,
			"average_rating" : data_entry[dat]['average_rating'],
			"evaluators" : data_entry[dat]['evaluators'],
		}
				
		data.append(row)

	return data
