// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Learning Session Evaluation Result"] = {
	"filters": [
		{
			"fieldname": "session",
			"label": __("Learning Session"),
			"fieldtype": "Link",
			"options": "Learning Session",
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
