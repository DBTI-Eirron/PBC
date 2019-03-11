# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	data = []

	from_event = frappe.db.sql("""SELECT DISTINCT LE.learning_program FROM `tabLearning Event` LE INNER JOIN `tabLearning Participants` LP ON LE.`name`=LP.`parent` 
		WHERE LE.event_status = "Completed" AND LP.employee = %s AND LE.docstatus = 1 """, (filters.employee), as_dict=True)
	for ev in from_event:
		data.append({"program":ev.learning_program,})

	from_wld = frappe.db.sql(""" SELECT DISTINCT WT.`training` FROM `tabWLD Needs Table` WT INNER JOIN `tabWLD Needs` WN WHERE WT.`status` = "Completed" AND WN.docstatus = 1 AND WT.employee = %s """, (filters.employee), as_dict=True)
	for wl in from_wld:
		data.append({"program":wl.training,})

	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "program",
			"label": _("Learning Program"),
			"fieldtype": "Data",
			"width": 500
		},
	]

	return columns