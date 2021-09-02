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
					"name": "Special Processing",
				},
				{
					"type": "doctype",
					"name": "Thirteenth Month Pay Processing",
				},
				{
					"type": "doctype",
					"name": "Leave Conversion",
				},
				{
					"type": "doctype",
					"name": "Adjustment Processing",
				},
				{
					"type": "doctype",
					"name": "Loan Application",
				},
				{
					"type": "doctype",
					"name": "Loan Restructure",
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
					"name": "Period Group",
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
				{
					"type": "doctype",
					"name": "Rate Classification",
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
				},{
					"type": "report",
					"name": "Payroll Register Per Department",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Payroll Register Per Cost Center",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Preliminary Report",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Loan Status",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "General Journal",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "13th Month",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "13th Month Pay Projection",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Pro Rated 13th Month",
					"doctype": "Last Pay Entry",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "YTD Payroll Report",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Net Payroll by Cost Center",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Hold Salaries Report",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "ER Share Journal Entry",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Payroll Summary Report Per Company",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Payroll Summary Report Per Work Location",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Payroll Summary Report per Payment Mode",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Corporate Payroll Summary",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Adjustment Report",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Minimum Take Home",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Bank Remittance",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Cash Remittance",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Cheque Remittance",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "YTD - Payroll Register Report",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},{
					"type": "report",
					"name": "Employee Daily Rate Report",
					"doctype": "Employee",	
					"is_query_report": True
				}
			],
		},
		{
			"label": _("Annualization"),
			"items": [
				{
					"type": "doctype",
					"name": "Annualization Processing",
				},			
				{
					"type": "report",
					"name": "Alphalist With Previous",	
					"is_query_report": True
				},
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
					"type": "doctype",
					"name": "Annualization Register",
				},					
			]
		},		
		{
			"label": _("Government Reports"),
			"items": [
				{
					"type": "report",
					"name": "BIR1601-C",
					"doctype": "Company",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "BIR1601-C per Company",
					"doctype": "Company",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "PagIbig Loan Report",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "PagIbig Summary Loan Report",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "PagIbig Premium Contribution",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "PagIbig Contribution Summary Report",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "PagIbig Remittance",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "PagIbig Loan Template",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "PagIbig Calamity Loan",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "SSS Loan Report",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "SSS Premium Contribution",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "SSS Calamity Loan",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "PhilHealth Premium Contribution",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "PhilHealth Remittance",	
					"is_query_report": True
				},
				{
					"type": "doctype",
					"name": "Government Certificate",	
				},{
					"type": "doctype",
					"name": "BIR1601 C Form",	
				},{
					"type": "doctype",
					"name": "BIR2316 Generator",	
				}
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
			"label": _("Tools"),
			"items": [							
				{
					"type": "doctype",
					"name": "Statement of Account",
				},
				{
					"type": "doctype",
					"name": "Payroll Process Logs",
				},
				{
					"type": "doctype",
					"name": "Payroll Register",
					"label": "Payroll Registers",
				},
				{
					"type": "doctype",
					"name": "Payroll Register Upload",
					"label": "Payroll Register Uploader",
				},
			]
		},

	]