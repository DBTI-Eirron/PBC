// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Appraisal Report"] = {
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
		/*{
			"fieldname": "start_date",
			"label": __("Start Date"),
			"fieldtype": "Date",
			"options": ""
		},
		{
			"fieldname": "end_date",
			"label": __("End Dates"),
			"fieldtype": "Date",
			"options": ""
		},
		{
			"fieldname": "com_date",
			"label": __("Date Completed"),
			"fieldtype": "Date",
			"options": ""
		},*/
	]
}
