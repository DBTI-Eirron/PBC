// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Alphalist With Previous"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"fieldname": "year",
			"label": __("Year"),
			"fieldtype": "Link",
			"options": "Payroll Year",
			"reqd": 1
		},
		{
			"fieldname": "schedule",
			"label": __("Schedule"),
			"fieldtype": "Select",
			"options": "\nSemi-Monthly\nMonthly\nWeekly",
			"reqd": 1
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"get_query": function() {
				var company = frappe.query_report_filters_by_name.company.get_value();
				return{
					filters: {
						'company': company
					}
				};
			}
		},	
	]
}
