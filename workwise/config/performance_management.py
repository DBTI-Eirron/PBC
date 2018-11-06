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
				# {
				# 	"type": "doctype",
				# 	"name": "Appraisal Template",
				# 	"description": _("Appraisal Template"),
				# },
				# {
				# 	"type": "doctype",
				# 	"name": "Appraisal Dates",
				# 	"description": _("Appraisal Dates"),
				# },
			]
		},
		{
		"label": _("Performance Planning"),
			"items": [
				{
					"type": "doctype",
					"name": "Target Setting",
					"description": _("Target Setting"),
				},
				{
					"type": "doctype",
					"name": "Target Setting Period",
					"description": _("Target Setting Period"),
				},
				{
					"type": "doctype",
					"name": "Target Standard",
					"description": _("Target Standard"),
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
					"name": "Tracking Individual Rating per Year",
					"doctype": "Tracking Individual Rating per Year",	
					"is_query_report": True
				},
			]
		},
	]