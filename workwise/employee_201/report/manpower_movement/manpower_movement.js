// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Manpower Movement"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"fieldname": "movement_type",
			"label": __("Movement Type"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Job Rotation", "label": __("Job Rotation") },
				{ "value": "Retirement", "label": __("Retirement") },
				{ "value": "Resignation", "label": __("Resignation") },
				{ "value": "Regularization", "label": __("Regularization") },
				{ "value": "Transfer", "label": __("Transfer") },
				{ "value": "Termination", "label": __("Termination") },
				{ "value": "Salary Adjustment", "label": __("Salary Adjustment") },
				{ "value": "Extension of Services", "label": __("Extension of Services") },
			],
			"default": "Job Rotation",
			"reqd": 1
		},
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
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
	]
}