from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Learning and Development"),
			"items": [
				{
					"type": "doctype",
					"name": "WLPD Plan",
					"description": _("WLPD Plan"),
				},
				{
					"type": "doctype",
					"name": "Training Needs Analysis",
					"description": _("Training Needs Analysis"),
				},
				{
					"type": "doctype",
					"name": "Learning Program",
					"description": _("Learning Program"),
				},
				{
					"type": "doctype",
					"name": "Learning Event",
					"description": _("Learning Event"),
				},
				{
					"type": "doctype",
					"name": "Learning Evaluation",
					"description": _("Learning Evaluation"),
				},
				{
					"type": "doctype",
					"name": "Learning Feedback",
					"description": _("Learning Feedback"),
				},
			]
		},
		{
			"label": _("Setup"),
			"items": [
				{
					"type": "doctype",
					"name": "Learning Objective",
					"description": _("Learning Objective"),
				},
				{
					"type": "doctype",
					"name": "Learning Course",
					"description": _("Learning Course"),
				},
				{
					"type": "doctype",
					"name": "Learning Provider",
					"description": _("Learning Provider"),
				},
			]
		},
		{
			"label": _("Reports"),
			"items": [
				{
					"type": "report",
					"name": "Training Needs Analysis Result",
					"doctype": "Training Needs Analysis",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Learning Event Result",
					"doctype": "Learning Event",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Learning Event Feedback",
					"doctype": "Learning Feedback",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Completed Learning Course",
					"doctype": "Completed Learning Course",	
					"is_query_report": True
				},
			]
		},
		{
			"label": _("Forms"),
			"items": [
				{
					"type": "doctype",
					"name": "Service Agreement Contract",
					"description": _("Service Agreement Contract"),
				},
				{
					"type": "doctype",
					"name": "Learning Request Form",
					"description": _("Learning Request Form"),
				},
				#{
				#	"type": "doctype",
				#	"name": "Executive Summary Report",
				#	"description": _("Executive Summary Report"),
				#},

			]
		},
	]