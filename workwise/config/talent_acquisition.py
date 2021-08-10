from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Talent Requisition Process"),
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
					"label": _("Schedules"),
					"description": _("Schedules and Assessment"),
				},	
				{
					"type": "doctype",
					"name": "Background Investigation",
				},	

				{
					"type": "doctype",
					"name": "Interview",
				},
				{
					"type": "doctype",
					"name": "Offer Letter",
				},
			]
		},
		{
			"label": _("Talent Acquisition Planning"),
			"items": [
				{
					"type": "doctype",
					"name": "Talent Acquisition Planning",
					"description": _("Talent Acquisition Planning"),
				},
				{
					"type": "doctype",
					"name": "Talent Requisition",
					"description": _("Talent Requisition"),
				},
				{
					"type": "doctype",
					"name": "Job Opening",
					"description": _("Job Opening"),
				},
				{
					"type": "report",
					"name": "Plantilla Report",
					"is_query_report": True
				},
			]
		},
		{
			"label": _("Tools"),
			"items": [
				{
					"type": "doctype",
					"name": "Job Opening Tool",
				},
			]
		},
	]