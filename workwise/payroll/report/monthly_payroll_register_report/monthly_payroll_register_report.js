// Copyright (c) 2016, OSI and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Monthly Payroll Register Report"] = {
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
			"label": __("Year"),
			"fieldtype": "Link",
			"options": "Payroll Year",
			"reqd": 1
		},
		{
			"fieldname": "payroll_month",
			"label": __("Month"),
			"fieldtype": "Select",
			"options": [
				{ "value": "1", "label": __("January") },
				{ "value": "2", "label": __("February") },
				{ "value": "3", "label": __("March") },
				{ "value": "4", "label": __("April") },
				{ "value": "5", "label": __("May") },
				{ "value": "6", "label": __("Jun") },
				{ "value": "7", "label": __("July") },
				{ "value": "8", "label": __("August") },
				{ "value": "9", "label": __("September") },
				{ "value": "10", "label": __("October") },
				{ "value": "11", "label": __("November") },
				{ "value": "12", "label": __("December") },
			],
			"default": "2",
			"reqd": 1
		},
		{
			"fieldname": "location",
			"label": __("Location"),
			"fieldtype": "Link",
			"options": "Location",
			"get_query": function() {
				var company = frappe.query_report.get_filter_value('company');
				return{
					filters: {
						'company': company
					}
				};
			},
			"reqd": 0
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"get_query": function() {
				var company = frappe.query_report.get_filter_value('company');
				return{
					filters: {
						'company': company
					}
				};
			}
		},
		{
			"fieldname": "value_precision",
			"label": __("Value Precision"),
			"fieldtype": "Select",
			"options": [
				{ "value": "2", "label": __("2") },
				{ "value": "3", "label": __("3") },
				{ "value": "4", "label": __("4") },
				{ "value": "5", "label": __("5") },
				{ "value": "6", "label": __("6") },
				{ "value": "7", "label": __("7") },
				{ "value": "8", "label": __("8") },
			],
			"default": "2",
			"reqd": 1
		},
		{
			"fieldname": "hide_zero",
			"label": __("Hide zero value"),
			"fieldtype": "Check",
		}
	]
};
