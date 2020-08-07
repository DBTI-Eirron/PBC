from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Reports"),
			"items": [
				{
					"type": "report",
					"name": "Attendance for the Day",
					"doctype": "Employee",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Movement Report",
					"doctype": "Employee",	
					"is_query_report": True
				}
			]
		},
	]