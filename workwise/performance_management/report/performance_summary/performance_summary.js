// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Performance Summary"] = {
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
			"options": "Payroll Year"
		},{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},{
			"fieldname": "rating",
			"label": __("Rating Classification"),
			"fieldtype": "Link",
			"options": "Rating Classification"
		},{
			"fieldname": "provi",
			"label": __("Probationary"),
			"fieldtype": "Check"
		}
	]
}
