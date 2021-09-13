// Copyright (c) 2016, OSI and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Adjustment Summary Processed"] = {
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
			"reqd": 1,
			"get_query": function() {
				var company = frappe.query_report_filters_by_name.company.get_value();
				var filters_list = {'company': company, 'status': "Closed"};
				return {filters: filters_list};
			},
		},
		{
			"fieldname": "current_payroll_period",
			"label": __("Current Payroll Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
			"reqd": 1,
			"get_query": function() {
				var company = frappe.query_report_filters_by_name.company.get_value();
				var filters_list = {'company': company, 'status': "Open"};
				return {filters: filters_list};
			},
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
			"get_query": function() {
				var company = frappe.query_report_filters_by_name.company.get_value();
				var show_active = frappe.query_report_filters_by_name.show_active.get_value();
				var filters_list = {'company': company};
				if (show_active){
					filters_list['is_active'] = '1';
				}
				return{filters: filters_list};
			},
		},
		{
			"fieldname": "time_options",
			"label": __("Options"),
			"fieldtype": "Data",
			"options": [
				{ "value": "Hrs	", "label": __("Hrs") }
			],
			"default": "Hrs",
			"reqd": 1
		},
		{
			"fieldname": "flt_precision",
			"label": __("Float Precision"),
			"fieldtype": "Int",
			"default": 4
		},
		{
			"fieldname": "show_active",
			"label": __("Show Active"),
			"fieldtype": "Check",
			"default": "1",
		},
	]
}
