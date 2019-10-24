// Copyright (c) 2016, OSI and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["13th Month Pay Projection"] = {
	"filters": [
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
			"fieldname": "payroll_year",
			"label": __("Payroll Year"),
			"fieldtype": "Link",
			"options": "Payroll Year",
			"reqd": 1
		},
		{
			"fieldname": "assume_last_month",
			"label": __("Last Month Paid"),
			"fieldtype": "Check",
		},
	]
}
