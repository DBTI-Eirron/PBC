// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

var today = new Date();
frappe.query_reports["My Daily Time Record"] = {
	"filters": [
		{
			"fieldname": "year",
			"label": __("Year"),
			"fieldtype": "Link",
			"options": "Payroll Year",
			"default": today.getFullYear(),
			"reqd": 1
		},
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"options": [
				{ "value": "0", "label": __("January") },
				{ "value": "1", "label": __("February") },
				{ "value": "2", "label": __("March") },
				{ "value": "3", "label": __("April") },
				{ "value": "4", "label": __("May") },
				{ "value": "5", "label": __("June") },
				{ "value": "6", "label": __("July") },
				{ "value": "7", "label": __("August") },
				{ "value": "8", "label": __("September") },
				{ "value": "9", "label": __("October") },
				{ "value": "10", "label": __("November") },
				{ "value": "11", "label": __("December") }
			],
			"default": today.getMonth(),
			"reqd": 1
		},
		{
			"fieldname": "payroll_period",
			"label": __("Payroll Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
			"reqd": 0
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
	]
}
