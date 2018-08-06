// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Preliminary Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"fieldname": "payroll_period",
			"label": __("Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
			"reqd": 1,
			"filters": {
				"status": 'Open'
			}
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
		},	
	]
}