// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Completed Learning Programs"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"reqd": 0,
			"on_change": function(query_report) {
				var employee = query_report.get_values().employee;
				if (!employee) {
					frappe.query_report_filters_by_name.employee_name.set_input("");
					query_report.trigger_refresh();
				}else {
					frappe.model.with_doc("Employee", employee, function(r) {
						var emp = frappe.model.get_doc("Employee", employee);
						frappe.query_report_filters_by_name.employee_name.set_input(emp.full_name);
						query_report.trigger_refresh();
					});
				}
			}
		},
		{
			"fieldname": "employee_name",
			"label": __("Employee Name"),
			"fieldtype": "Data",
			"read_only": 1
		},
	]
}
