// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Net Payroll by Cost Center"] = {
	"filters": [
		{
			"fieldname": "period",
			"label": __("Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
			"reqd": 1
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"reqd": 1
		},
		{
			"fieldname": "value_precision",
			"label": __("Value Precision"),
			"fieldtype": "Select",
			"options": [
				{ "value": "2", "label": __("2") },
				{ "value": "3", "label": __("3") },
				{ "value": "4", "label": __("4") },
				{ "value": "5", "label": __("5") },
				{ "value": "6", "label": __("6") },
				{ "value": "7", "label": __("7") },
				{ "value": "8", "label": __("8") },
			],
			"default": "2",
			"reqd": 1
		},
	]
}
