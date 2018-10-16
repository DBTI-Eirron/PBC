from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Recruitment"),
			"items": [
				{
					"type": "page",
					"name": "applicant_monitoring",
					"label": _("Applicant Monitoring"),
				},
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
					"name": "Interview and Background",
					"label": _("Interview and Background"),
				},
				{
					"type": "doctype",
					"name": "Offer Letter",
					"description": _("Offer Letter"),
				},
			]
		},
		{
			"label": _("Tools"),
			"items": [
				{
					"type": "doctype",
					"name": "Personnel Requisition",
					"description": _("Personnel Requisition"),
				},
				{
					"type": "doctype",
					"name": "Job Opening",
					"description": _("Job Opening"),
				},
				{
					"type": "report",
					"name": "Plantilla Report",
					"doctype": "Plantilla Report",	
					"is_query_report": True
				},
			]
		},
	]