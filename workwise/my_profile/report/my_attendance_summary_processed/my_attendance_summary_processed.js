// Copyright (c) 2016, OSI and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["My Attendance Summary Processed"] = {
	"filters": [
		{
			"fieldname": "payroll_period",
			"label": __("Payroll Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
			"reqd": 1
		},
		{
			"fieldname": "time_options",
			"label": __("Options"),
			"fieldtype": "Data",
			"options": [
				{ "value": "Hrs	", "label": __("Hrs") }
			],
			"default": "Hrs",
			"reqd": 1
		},
		{
			"fieldname": "flt_precision",
			"label": __("Float Precision"),
			"fieldtype": "Int",
			"default": function(query_report) {
				frappe.model.get_value('Timekeeping Settings', {'name': 'Timekeeping Settings'}, 'default_decimal_places',
				function(d) {
					frappe.query_report_filters_by_name.flt_precision.set_input(d.default_decimal_places);
					if (!d.default_decimal_places){
						frappe.query_report_filters_by_name.flt_precision.set_input(2);
					}
					query_report.trigger_refresh();
				})
			},
		},
		{
			"fieldname": "show_break",
			"label": __("Show Break Time"),
			"fieldtype": "Check",
		},
	]
}
