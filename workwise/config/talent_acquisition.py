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