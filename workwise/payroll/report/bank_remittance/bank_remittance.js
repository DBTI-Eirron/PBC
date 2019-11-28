// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Bank Remittance"] = {
	"filters": [
		{
			"fieldname": "bank",
			"label": __("Bank"),
			"fieldtype": "Link",
			"options": "Bank",
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
			"fieldname": "payroll_period",
			"label": __("Payroll Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
			"reqd": 1,
			"get_query": function() {
				var company = frappe.query_report_filters_by_name.company.get_value();
				return{
					filters: {
						'company': company,
						"status": 'Closed'
					}
				};
			},
			"reqd": 1
		},
		{
			"fieldname": "location",
			"label": __("Location"),
			"fieldtype": "Link",
			"options": "Location",
		},
		{
			"fieldname": "bank_type",
			"label": __("Bank Type"),
			"fieldtype": "Select",
			"options": [
				{ "value": "All", "label": __("All") },
				{ "value": "Current", "label": __("Current") },
				{ "value": "Savings", "label": __("Savings") },
				{ "value": "Cash Card", "label": __("Cash Card") }
			],
			"default": "All",
			"reqd": 0
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
			"fieldname": "include_header",
			"label": __("Include Header"),
			"fieldtype": "Check",
		},
	]
}
