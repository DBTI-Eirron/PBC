from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Dashboard"),
			"items": [
				{
					"type": "doctype",
					"name": "Dashboard",
					"description": _("Dashboard"),
				},
			],
		},
	]