# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, today

def execute(filters=None):
	columns = get_columns(filters)
	result = get_result(filters)
	return columns, result

def get_columns(filters):
	columns = [{
		"fieldname":"target_setting_period",
		"label": _("Target Setting Period"),
		"fieldtype": "Data",
		"width": 160
	}]
	department = frappe.db.sql("""SELECT `name` FROM `tabDepartment`""",as_dict=True)
	for d in department:
		columns += [{
			"fieldname": d.name,
			"label": _(d.name),
			"fieldtype": "Data",
			"width": 160
		}]
	return columns

def get_result(filters):
	result = []
	period = frappe.db.sql("""SELECT `name`,to_date,from_date FROM `tabPayroll Year`""",as_dict=True)
	for x in period:
		row = {}
		row.update({"target_setting_period":x.name})
		department = frappe.db.sql("""SELECT `name` FROM `tabDepartment`""",as_dict=True)
		for d in department:
			total_score =  frappe.db.sql("""SELECT SUM(total_score)as total,(SELECT COUNT(total_score) FROM `tabAppraisal` WHERE department = %s AND company = %s AND from_date BETWEEN %s AND %s)as count FROM `tabAppraisal` WHERE department = %s AND company = %s AND from_date BETWEEN %s AND %s LIMIT 1""",(d.name,filters.company,x.from_date,x.to_date,d.name,filters.company,x.from_date,x.to_date),as_dict=True)
			for t in total_score:
				if t.total:
					avg = t.total / t.count
					row.update({d.name:'{:.2f}'.format(avg)})
		result.append(row)
	return result