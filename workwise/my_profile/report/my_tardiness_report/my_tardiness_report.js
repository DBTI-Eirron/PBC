// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["My Tardiness Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "time_options",
			"label": __("Options"),
			"fieldtype": "Data",
			"options": [
				
				{ "value": "Hrs	", "label": __("Hrs") },
			],
			"default": "Hrs",
			"reqd": 1
		}
	]
}
