// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["WLD Needs Monitoring"] = {
	"filters": [
		{
			"fieldname": "wld_needs",
			"label": __("WLD Needs"),
			"fieldtype": "Link",
			"options": "WLD Needs",
			"reqd": 1
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
	]
}
