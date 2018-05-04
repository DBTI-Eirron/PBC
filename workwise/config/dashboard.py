from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Dashboard"),
			"items": [
				{
					"type": "report",
					"name": "test report",
					"doctype": "User",	
					"is_query_report": True
				},
				{
					"type": "doctype",
					"name": "Dashboard",
					"description": _("Dashboard"),
				},
			],
		},
	]