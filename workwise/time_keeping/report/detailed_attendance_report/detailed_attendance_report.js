// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Detailed Attendance Report"] = {
	"filters": [
		{
			"fieldname": "payroll_period",
			"label": __("Payroll Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
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
				{ "value": "Hrs", "label": __("Hrs") },
				{ "value": "Mins", "label": __("Mins") }
			],
			"default": "Hrs",
			"reqd": 1
		},
	]
}
