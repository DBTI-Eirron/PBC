# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str

def execute(filters=None):
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 140
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 250
		},
		{
			"fieldname": "med_type",
			"label": _("Medication Type"),
			"fieldtype": "Link",
			"options": "Medication Type",
			"width": 140
		},
		{
			"fieldname": "med_provider",
			"label": _("Health Provider"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "med_completion",
			"label": _("Completion"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "med_status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 140
		},
	]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_schedule(filters, pay_from, pay_to):
	

	return data

def get_data(filters):
	#Initialize
	data = []

	record = frappe.db.sql("""SELECT
		MR.`employee`,
		TE.`full_name`,
		MR.`med_type`,
		MR.`med_provider`,
		MR.`med_completion`,
		MR.`med_status` 
	FROM
		`tabEmployee Medical Record` MR
		JOIN tabEmployee TE 
	WHERE
		TE.`name` = MR.`employee` 
		AND TE.`company` = %(company)s""",
		{
		"company": filters.company,
	}, as_dict=True)

	for a in record: 
		entry = {
			"employee": a.employee,
			"med_type": a.med_type,
			"med_provider": a.med_provider,
			"med_completion": a.med_completion,
			"med_status": a.med_status,
			"employee_name": a.full_name,
		}
		data.append(entry)

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = {
			"employee": d.get("employee"),
			"med_type": d.get("med_type"),
			"med_provider": d.get("med_provider"),
			"med_completion": d.get("med_completion"),
			"med_status": d.get("med_status"),			
			"employee_name": d.get("employee_name"),
		}
		
		result.append(row)
	return result