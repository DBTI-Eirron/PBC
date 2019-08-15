# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import get_schedule

def execute(filters=None):
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):
	columns = [
		{
			"fieldname": "work_shift",
			"label": _("Shift"),
			"fieldtype": "Link",
			"options": "Work Shift",
			"width": 140
		},
		{
			"fieldname": "pre_shift",
			"label": _("PRE"),
			"fieldtype": "Data",
			"width": 140
		},

		{
			"fieldname": "time_in",
			"label": _("Time IN"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "break_start",
			"label": _("Break Start"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "break_end",
			"label": _("Break End"),
			"fieldtype": "Data",
			"width": 140
		},	
		{
			"fieldname": "time_out",
			"label": _("Time Out"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "post_shift",
			"label": _("POST"),
			"fieldtype": "Data",
			"width": 140
		},
	]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_data(filters):
	#Initialize
	data = []

	pay_from, pay_to = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to"])
	schedule = get_schedule(filters.employee, pay_from, pay_to)
	for sched in schedule:
		pre_shift, post_shift = frappe.db.get_value("Work Shift", sched['work_shift'], ["setup_preshift", "end_postshift"]) 
		entry = {
			"work_shift": sched['work_shift'],
			"time_in": sched['datetime_in'],
			"time_out": sched['datetime_out'],
			"break_start": sched['break_start'],
			"break_end": sched['break_end'],
			"pre_shift": add_to_date(sched['datetime_in'], hours=(0 - pre_shift) ),
			"post_shift": add_to_date(sched['datetime_out'], hours=post_shift ),	
		}
		data.append(entry)

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = {
			"work_shift": d.get("work_shift"),
			"pre_shift": d.get("pre_shift"),
			"post_shift": d.get("post_shift"),
			"time_in": d.get("time_in"),
			"time_out": d.get("time_out"),
			"break_start": d.get("break_start"),			
			"break_end": d.get("break_end"),
		}
		
		result.append(row)
	return result