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
			"options": "Employee",
			"get_query": function() {
				var company = frappe.query_report_filters_by_name.company.get_value();
				return{
					filters: {
						'company': company,
					}
				};
			},
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
