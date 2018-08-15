from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("My Payroll"),
			"items": [
				{
					"type": "doctype",
					"name": "My Payslip",
					"description": _("Payslip List"),
				},
				{
					"type": "report",
					"name": "My Contributions",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "My Tax",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "My Loans",
					"doctype": "Payroll Register",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "My Daily Time Record",
					"doctype": "Time Card",	
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "My Tardiness Report",
					"doctype": "Work Schedule",	
					"is_query_report": True
				},
			]
		},
	]
