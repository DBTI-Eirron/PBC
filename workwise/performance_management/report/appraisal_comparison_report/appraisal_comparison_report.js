// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Appraisal Comparison Report"] = {
	"filters": [
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"reqd": 1
		},
		{
			"fieldname": "appraisal_dates",
			"label": __("Appraisal Dates"),
			"fieldtype": "Link",
			"options": "Appraisal Dates",
			"reqd": 1
		},

	]
}
