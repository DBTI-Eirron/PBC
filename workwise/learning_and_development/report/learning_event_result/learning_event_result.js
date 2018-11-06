// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Learning Event Result"] = {
	"filters": [
		{
			"fieldname": "training_name",
			"label": __("Event Name"),
			"fieldtype": "Link",
			"options": "Learning Event",
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
