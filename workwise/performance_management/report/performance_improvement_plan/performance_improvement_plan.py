# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	data = get_data(filters)
	columns = get_columns(filters)
	return columns, data

def get_columns(filters):
	columns = [
	{
		"fieldname":"appraisal",
		"label": _("Appraisal"),
		"fieldtype": "Data",
		"width": 160
	},
	{
		"fieldname":"appraisee",
		"label": _("Appraisee"),
		"fieldtype": "Data",
		"width": 160
	},
	{
		"fieldname":"appraisee_name",
		"label": _("Appraisee Name"),
		"fieldtype": "Data",
		"width": 160
	},]
	KRA = frappe.db.sql("""SELECT key_result_area FROM `tabPerformance Planning KRA` WHERE parent = %s""",(filters.target_setting),as_dict=True)
	for d in KRA:
		columns += [{
			"fieldname": d.key_result_area,
			"label": _(d.key_result_area),
			"fieldtype": "Data",
			"width": 200
		}]
	return columns

def get_data(filters):
	indicators = frappe.db.sql("""SELECT key_indicator FROM `tabPerformance Planning KI` WHERE parent  = %s """,(filters.target_setting),as_dict=True)
	appraisals = frappe.db.sql("""SELECT appraisee, appraisee_name FROM `tabAppraisal` WHERE target_setting  = %s """,(filters.target_setting),as_dict=True)

	return []