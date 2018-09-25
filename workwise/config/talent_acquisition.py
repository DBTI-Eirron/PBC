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
					"name": "Schedules and Assessment",
					"description": _("Schedules and Assessment"),
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
					"type": "page",
					"name": "applicant_monitoring",
					"label": _("Applicant Monitoring"),
				},	
				{
					"type": "page",
					"name": "interview_and_background",
					"label": _("Interview and Background"),
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