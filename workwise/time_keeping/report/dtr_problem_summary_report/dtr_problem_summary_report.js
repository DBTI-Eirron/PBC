// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["DTR Problem Summary Report"] = {
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
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
		},
		{
			"fieldname": "location",
			"label": __("Location"),
			"fieldtype": "Link",
			"options": "Location",
		},
		{
			"fieldname": "position_title",
			"label": __("Position Title"),
			"fieldtype": "Link",
			"options": "Position Title",
		},
				{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
		},
		{
			"fieldname": "period_group",
			"label": __("Period Group"),
			"fieldtype": "Link",
			"options": "Period Group",
		},
	]
};
