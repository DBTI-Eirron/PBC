from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Work Shift and Schedules"),
			"items": [
				{
					"type": "doctype",
					"name": "Work Shift",
				},
				{
					"type": "doctype",
					"name": "Work Schedule Template",
				},
				{
					"type": "doctype",
					"name": "Work Schedule Assignment",
				},
				{
					"type": "doctype",
					"name": "Time Card",
				},
				{
					"type": "doctype",
					"name": "Attendance Processing",
				},
				{
					"type": "doctype",
					"name": "Attendance Register",
				},
			]
		},
		{
			"label": _("Applications"),
			"items": [
				{
					"type": "doctype",
					"name": "Leave Application",
				},
				{
					"type": "doctype",
					"name": "Overtime Application",
				},
				{
					"type": "doctype",
					"name": "Official Business Application",
				},
				{
					"type": "doctype",
					"name": "Change Schedule Application",
				},
				{
					"type": "doctype",
					"name": "Blanket",
				},
			]
		},
		{
			"label": _("Setup"),
			"items": [
				{
					"type": "doctype",
					"name": "Timekeeping Settings",
				},		
				{
					"type": "doctype",
					"name": "Biometrics Upload",
				},			
				{
					"type": "doctype",
					"name": "Leave Balance",
				},
				{
					"type": "doctype",
					"name": "Leave Type",
				},
				{
					"type": "doctype",
					"name": "Overtime Type",
				},
				{
					"type": "doctype",
					"name": "Holiday",
				},
			]
		},
		{
			"label": _("Reports"),
			"items": [
				{
					"type": "report",
					"name": "Attendance Summary",
					"doctype": "Work Schedule",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Attendance Summary Processed",
					"doctype": "Attendance Register",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Employee Schedule",
					"doctype": "Work Schedule",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Leave Balance Report",
					"doctype": "Leave Balance Report",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Employee Tardiness Report",
					"doctype": "Attendance Register",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Tardiness Frequency Report",
					"doctype": "Attendance Register",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Tardiness Summary Report",
					"doctype": "Attendance Register",	
					"is_query_report": True
				},
			],
		},	
	]