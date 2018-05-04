from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Employee Info"),
			"items": [
							{
					"type": "page",
					"name": "dashboard",
					"label": _("Dashboard")
				},
				{
					"type": "doctype",
					"name": "Employee",
					"description": _("Employee"),
				},
				{
					"type": "doctype",
					"name": "Employee Subordinates",
					"description": _("Employee Subordinates"),
				},
				{
					"type": "doctype",
					"name": "Department",
					"icon": "fa fa-sitemap",
					"label": _("Organization Structure"),
					"route": "Tree/Department",
				},
			]
		},
		{
			"label": _("Organization"),
			"items": [
				{
					"type": "doctype",
					"name": "Company",
					"description": _("Company"),
				},
				{
					"type": "doctype",
					"name": "Job Level",
					"description": _("Job Level"),
				},
				{
					"type": "doctype",
					"name": "Position Title",
					"description": _("Position Title"),
				},
				{
					"type": "doctype",
					"name": "Employment Status",
					"description": _("Employment Status"),
				},
				{
					"type": "doctype",
					"name": "Project",
					"description": _("Project"),
				},
			]
		},
		{
			"label": _("Location"),
			"items": [
				{
					"type": "doctype",
					"name": "Location",
					"description": _("Location"),
				}
			]
		},
		{
			"label": _("Employee Medical"),
			"items": [
				{
					"type": "doctype",
					"name": "Employee Medical Record",
					"description": _("Location"),
				},
				{
					"type": "doctype",
					"name": "Medication Type",	
				},
			]
		},

	]