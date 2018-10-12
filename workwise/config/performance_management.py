from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Appraisal"),
			"items": [
				{
					"type": "doctype",
					"name": "Appraisal",
					"description": _("Appraisal"),
				},
				{
					"type": "doctype",
					"name": "Appraisal Template",
					"description": _("Appraisal Template"),
				},
				{
					"type": "doctype",
					"name": "Appraisal Dates",
					"description": _("Appraisal Dates"),
				},
				{
					"type": "report",
					"name": "Appraisal Comparison Report",
					"doctype": "Appraisal Comparison Report",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Appraisal Report",
					"doctype": "Appraisal Report",	
					"is_query_report": True
				},
			]
		},
	]