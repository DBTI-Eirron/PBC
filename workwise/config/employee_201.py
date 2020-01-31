from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Employee Info"),
			"items": [
				{
					"type": "doctype",
					"name": "Employee",
					"description": _("Employee"),
				},
				{
					"type": "doctype",
					"name": "Employee Medical Record",
					"description": _("Location"),
				},
				{
					"type": "doctype",
					"name": "Change Request Application",
					"description": _("Change Request Application"),
				},
				{
					"type": "doctype",
					"name": "Certificate of Employment",
					"description": _("Certificate of Employment"),
				},
				{
					"type": "doctype",
					"name": "Certificate of Maternity",
					"description": _("Certificate of Maternity"),
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
					"name": "Department",
					"icon": "fa fa-sitemap",
					"label": _("Department"),
					"route": "Tree/Department",
					"description": _("Tree of Organization Structure."),
				},
				{
					"type": "doctype",
					"name": "Location",
					"description": _("Location"),
				},
				#{
				#	"type": "doctype",
				#	"name": "Cost Center",
				#	"description": _("Cost Center"),
				#},
				{
					"type": "doctype",
					"name": "Cost Center",
					"icon": "fa fa-sitemap",
					"label": _("Cost Center"),
					"route": "Tree/Cost Center",
					"description": _("Tree of Cost Centers."),
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
					"name": "Notice to Explain",
					"description": _("Notice to Explain"),
				},
				{
					"type": "doctype",
					"name": "Memo",
					"description": _("Memo"),
				},
			]
		},
		{
			"label": _("Movement"),
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
			"label": _("Employee Medical"),
			"items": [

			]
		},
		{
			"label": _("Setup"),
			"items": [
				{
					"type": "doctype",
					"name": "Employee Record Settings",				},
				{
					"type": "doctype",
					"name": "Employee Subordinates",
					"description": _("Employee Subordinates"),
				},
				{
					"type": "doctype",
					"name": "Sensitivity Level",
				},
				{
					"type": "doctype",
					"name": "Medication Type",	
				},
			]
		},
		{
			"label": _("Reports"),
			"items": [
				{
					"type": "report",
					"name": "Plantilla Report",
					"doctype": "Employee",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Manpower Count",
					"doctype": "Employee",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Manpower Movement",
					"doctype": "Employee Movement",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Employee Listing",
					"doctype": "Employee",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "APE Compliance Report",
					"doctype": "Employee Medical Record",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Retireable Employees",
					"doctype": "Employee Movement",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Gender per Company",
					"doctype": "Gender per Company",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Age per Company",
					"doctype": "Age per Company",	
					"is_query_report": True
				},
			]
		},

	]