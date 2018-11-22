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
			]
		},
		{
		"label": _("Other Forms"),
			"items": [
				{
					"type": "doctype",
					"name": "Peer Assessment",
					"description": _("Peer Assessment"),
				},
				{
					"type": "doctype",
					"name": "Core Values Practice",
					"description": _("Core Values Practice"),
				},
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
					"name": "Appraisal Settings",
					"description": _("Appraisal Settings"),
				},
				{
					"type": "doctype",
					"name": "Peer Assessment Settings",
					"description": _("Peer Assessment Settings"),
				},
				{
					"type": "doctype",
					"name": "Core Values Practice Settings",
					"description": _("Core Values Practice Settings"),
				},
				{
					"type": "doctype",
					"name": "Rating Classification",
					"description": _("Rating Classification"),
				},
			]
		},
	]