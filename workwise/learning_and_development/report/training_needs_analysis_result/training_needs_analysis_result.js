// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Training Needs Analysis Result"] = {
	"filters": [
		{
			"fieldname": "training_name",
			"label": __("Training Name"),
			"fieldtype": "Link",
			"options": "Training Needs Analysis",
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
