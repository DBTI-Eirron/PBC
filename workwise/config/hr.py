from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Recruitment"),
			"items": [
				{
					"type": "doctype",
					"name": "Job Applicant",
					"description": _("Job Applicant"),
				},
				{
					"type": "doctype",
					"name": "Job Opening",
					"description": _("Job Opening"),
				},
				{
					"type": "doctype",
					"name": "Offer Letter",
					"description": _("Offer Letter"),
				},
				{
					"type": "doctype",
					"name": "Personnel Requisition",
					"description": _("Personnel Requisition"),
				},
				{
					"type": "report",
					"name": "Applicant Monitoring",
					"doctype": "Applicant Monitoring",	
					"is_query_report": True
				},
			]
		},
		{
			"label": _("Training and Development"),
			"items": [
				{
					"type": "doctype",
					"name": "Training Course",
					"description": _("Training Course"),
				},
				{
					"type": "doctype",
					"name": "Training Event",
					"description": _("Training Event"),
				},
				{
					"type": "doctype",
					"name": "Training Evaluation",
					"description": _("Training Evaluation"),
				},
			]
		},
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
				{
					"type": "doctype",
					"name": "Team Updates",
					"description": _("Team Updates"),
				},
			]
		},
		{
			"label": _("Employee Adjustments"),
			"items": [
				{
					"type": "doctype",
					"name": "Employee Movement",
					"description": _("Employee Movement"),
				},
				{
					"type": "doctype",
					"name": "Exit Interview",
					"description": _("Exit Interview"),
				},
			]
		},
		{
			"label": _("Code of Conduct"),
			"items": [
				{
					"type": "doctype",
					"name": "Incident Report",
					"description": _("Incident Report"),
				},
				{
					"type": "doctype",
					"name": "Disciplinary Action",
					"description": _("Disciplinary Action"),
				},
				{
					"type": "doctype",
					"name": "Memo",
					"description": _("Memo"),
				},
			]
		},
		{
			"label": _("Reports"),
			"items": [
				{
					"type": "report",
					"name": "Plantilla Report",
					"doctype": "Plantilla Report",	
					"is_query_report": True
				},
			]
		},
	]