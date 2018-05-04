from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Payroll Processing"),
			"items": [
				{
					"type": "doctype",
					"name": "Payroll Processing",
				},
				{
					"type": "doctype",
					"name": "Loan Application",
				},
				{
					"type": "doctype",
					"name": "Recurring Entry",
				},
				{
					"type": "doctype",
					"name": "Batch Entry",
				},
			]
		},
		{
			"label": _("Payroll Setup"),
			"items": [
				{
					"type": "doctype",
					"name": "Payroll Year",
				},
				{
					"type": "doctype",
					"name": "Payroll Period",
				},
				{
					"type": "doctype",
					"name": "Transaction Type",
				},
				{
					"type": "doctype",
					"name": "Overtime Rates",
				},
				{
					"type": "doctype",
					"name": "Account",
					"icon": "fa fa-sitemap",
					"label": _("Chart of Accounts"),
					"route": "Tree/Account",
					"description": _("Tree of financial accounts."),
				},
			]
		},
		{
			"label": _("Payroll Reports"),
			"items": [
				{
					"type": "report",
					"name": "Payroll Register Report",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Loan Status",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "General Journal",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "13th Month Basis",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "YTD Payroll Report",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},
			],
		},
		{
			"label": _("Government Reports"),
			"items": [
				{
					"type": "report",
					"name": "PagIbig Premium Contribution",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "SSS Premium Contribution",
					"doctype": "SSS Premium Contribution",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "PhilHealth Premium Contribution",
					"doctype": "PhilHealth Premium Contribution",	
					"is_query_report": True
				},
			],
		},
		{
			"label": _("Government Setup"),
			"items": [
				{
					"type": "doctype",
					"name": "SSS Setup",
				},			
				{
					"type": "doctype",
					"name": "PHIC Setup",
				},
				{
					"type": "doctype",
					"name": "HDMF Setup",
				},
				{
					"type": "doctype",
					"name": "TRAIN Setup",
				},
			]
		}
	]