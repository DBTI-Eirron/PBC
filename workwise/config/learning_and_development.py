from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Learning and Development"),
			"items": [
				{
					"type": "doctype",
					"name": "WLD Needs",
					"description": _("WLD Needs"),
				},
				{
					"type": "doctype",
					"name": "Training Needs Analysis",
					"description": _("Training Needs Analysis"),
				},
				{
					"type": "doctype",
					"name": "Learning Event",
					"description": _("Learning Event"),
				},
				{
					"type": "doctype",
					"name": "Evaluation for Learners",
					"description": _("Evaluation for Learners"),
				},
				{
					"type": "doctype",
					"name": "Learning Session Evaluation",
					"description": _("Learning Session Evaluation"),
				},
			]
		},
		{
			"label": _("Setup"),
			"items": [
				{
					"type": "doctype",
					"name": "Learning Program",
					"description": _("Learning Program"),
				},
				{
					"type": "doctype",
					"name": "Learning Session",
					"description": _("Learning Session"),
				},
				{
					"type": "doctype",
					"name": "Learning Methodology",
					"description": _("Learning Methodology"),
				},
			]
		},
		{
			"label": _("Reports"),
			"items": [
				{
					"type": "report",
					"name": "WLD Needs Monitoring",
					"doctype": "WLD Needs",	
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
					"name": "Learning Session Evaluation Result",
					"doctype": "Learning Session Evaluation",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Completed Learning Programs",
					"doctype": "Learning Event",	
					"is_query_report": True
				},
			]
		},
		{
			"label": _("Forms"),
			"items": [
				{
					"type": "doctype",
					"name": "Certificate of Training",
					"description": _("Certificate of Training"),
				},
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
				{
					"type": "doctype",
					"name": "Executive Summary Report",
					"description": _("Executive Summary Report"),
				},

			]
		},
	]