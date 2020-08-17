// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Leave Balance Summary Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"fieldname": "year",
			"label": __("Year"),
			"fieldtype": "Link",
			"options": "Payroll Year",
			"reqd": 1
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname": "period_group",
			"label": __("Period Group"),
			"fieldtype": "Link",
			"options": "Period Group"
		},
		{
			"fieldname": "location",
			"label": __("Location"),
			"fieldtype": "Link",
			"options": "Location"
		},
	]
}