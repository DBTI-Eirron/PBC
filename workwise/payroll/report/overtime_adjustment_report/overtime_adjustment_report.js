// Copyright (c) 2016, OSI and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Overtime Adjustment Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"fieldname": "previous_payroll_period",
			"label": __("Previous Payroll Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
			"reqd": 1
		},
		{
			"fieldname": "current_payroll_period",
			"label": __("Current Payroll Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
			"reqd": 1
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname": "date",
			"label": __("Date"),
			"fieldtype": "Date",
		},
		{
			"fieldname": "type_of_overtime",
			"label": __("Type of Overtime"),
			"fieldtype": "Link",
			"options": "Overtime Rates"
		},
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch"
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "position_title",
			"label": __("Position Title"),
			"fieldtype": "Link",
			"options": "Position Title"
		},
	]
}
