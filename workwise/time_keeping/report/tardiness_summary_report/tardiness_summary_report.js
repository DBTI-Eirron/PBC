// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Tardiness Summary Report"] = {
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
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
		},
		{
			"fieldname": "time_options",
			"label": __("Options"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Mins", "label": __("Mins") },
				{ "value": "Hrs	", "label": __("Hrs") }
			],
			"default": "Mins",
			"reqd": 1
		},
		{
			"fieldname": "period_group",
			"label": __("Period Group"),
			"fieldtype": "Link",
			"options": "Period Group",
		},
	]
}
