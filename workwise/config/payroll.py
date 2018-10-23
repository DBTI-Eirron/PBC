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
				{
					"type": "doctype",
					"name": "Last Pay Entry",
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
					"name": "Bank",
				},
				{
					"type": "doctype",
					"name": "Alphalist Consideration",
				},
				{
					"type": "doctype",
					"name": "Payroll Settings",
				},
				{
					"type": "doctype",
					"name": "System Policy",
				},
				{
					"type": "doctype",
					"name": "Account",
					"icon": "fa fa-sitemap",
					"label": _("Chart of Accounts"),
					"route": "Tree/Account",
					"description": _("Tree of financial accounts."),
				},
				{
					"type": "doctype",
					"name": "Bank Remittance Setup",
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
					"name": "Payroll Register Per Department",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Preliminary Report",
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
				{
					"type": "report",
					"name": "Bank Remittance",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Net Payroll by Cost Center",
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
					"name": "Alphalist With No Previous",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Alphalist Terminated",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Alphalist Minimum Wage",	
					"is_query_report": True
				},	
				{
					"type": "report",
					"name": "PagIbig Loan Report",	
					"is_query_report": True
				},	
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
					"name": "BIR2316",
				},	
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
		},		
		{
			"label": _("Utilities"),
			"items": [
				{
					"type": "doctype",
					"name": "Statement of Account",
				},
				{
					"type": "doctype",
					"name": "Payroll Process Logs",
				},
			]
		},

	]