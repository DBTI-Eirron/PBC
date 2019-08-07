from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Evaluation"),
			"items": [
				{
					"type": "doctype",
					"name": "Evaluation",
					"description": _("Evaluation"),
				},
				{
					"type": "doctype",
					"name": "Target Settings",
					"description": _("Target Settings"),
				},
			]
		},
		{
		"label": _("Reports"),
			"items": [
				{
					"type": "report",
					"name": "Comparison per Department",
					"doctype": "Comparison per Department",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Individual Rating Summary",
					"doctype": "Individual Rating Summary",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Performance Summary",
					"doctype": "Performance Summary",	
					"is_query_report": True
				},
			]
		},
		{
		"label": _("Other Forms"),
			"items": [
				{
					"type": "doctype",
					"name": "Performance Improvement Plan",
					"description": _("Performance Improvement Plan"),
				},
			]
		},
		{
		"label": _("Setups"),
			"items": [
				{
					"type": "doctype",
					"name": "Rating Classification",
					"description": _("Rating Classification"),
				},
				{
					"type": "doctype",
					"name": "Target Standard",
					"description": _("Target Standard"),
				},

			]
		},
	]