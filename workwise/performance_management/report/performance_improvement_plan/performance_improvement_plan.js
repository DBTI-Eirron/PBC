// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Performance Improvement Plan"] = {
	"filters": [
			{
			"fieldname": "target_setting",
			"label": __("Target Setting"),
			"fieldtype": "Link",
			"options": "Target Setting",
			"reqd": 1
		},
	]
}
