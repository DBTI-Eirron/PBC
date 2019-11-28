// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Payroll Summary Report per Payment Mode"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1
		},{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1
		},{
			"fieldname": "position_title",
			"label": __("Position Title"),
			"fieldtype": "Link",
			"options": "Position Title",
		},{
			"fieldname": "mode_of_payment",
			"label": __("Mode of Payment"),
			"fieldtype": "Select",
			"options":["BANK","CASH","ON HOLD"]
		},{
			"fieldname": "value_precision",
			"label": __("Value Precision"),
			"fieldtype": "Select",
			"options": [
				{ "value": "2", "label": __("2") },
				{ "value": "3", "label": __("3") },
				{ "value": "4", "label": __("4") },
				{ "value": "5", "label": __("5") },
				{ "value": "6", "label": __("6") },
				{ "value": "7", "label": __("7") },
				{ "value": "8", "label": __("8") },
			],
			"default": "2",
			"reqd": 1
		},
	]
}
