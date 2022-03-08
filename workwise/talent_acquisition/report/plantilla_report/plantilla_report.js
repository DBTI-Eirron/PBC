// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Plantilla Report"] = {
		"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"fieldname":"location",
			"label": __("Location"),
			"fieldtype": "Link",
			"options": "Location",
			"get_query": function() {
				var company = frappe.query_report_filters_by_name.company.get_value();
				return{
					filters: {
						'company': company,
					}
				};
			},
		},
		{
			"fieldname":"department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"get_query": function() {
				var company = frappe.query_report_filters_by_name.company.get_value();
				return{
					filters: {
						'company': company,
					}
				};
			},
		},
	]
}
