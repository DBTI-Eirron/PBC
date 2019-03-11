// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Rewards and Recognition"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"fieldname": "payroll_year",
			"label": __("Payroll Year"),
			"fieldtype": "Link",
			"options": "Payroll Year",
			"reqd": 1
		},
		{
			fieldname: "period",
			label: __("Period"),
			fieldtype: "Select",
			options: [
				{ "value": "Quarterly", "label": __("Quarterly") },
				{ "value": "Half-Yearly", "label": __("Half-Yearly") },
				{ "value": "Yearly", "label": __("Yearly") }
			],
			default: "Quarterly"
		},
	]
}
