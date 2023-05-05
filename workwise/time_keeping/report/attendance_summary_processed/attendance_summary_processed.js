frappe.query_reports["Attendance Summary Processed"] = {
	"filters": [
		{
			"fieldname": "payroll_period",
			"label": __("Payroll Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
			"reqd": 1
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"fieldtype": "Break",
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
		},
		{
			"fieldname": "location",
			"label": __("Location"),
			"fieldtype": "Link",
			"options": "Location",
		},
		{
			"fieldname": "position_title",
			"label": __("Position Title"),
			"fieldtype": "Link",
			"options": "Position Title",
		},
		{
			"fieldname": "time_options",
			"label": __("Options"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Mins", "label": __("Mins") },
				{ "value": "Hrs	", "label": __("Hrs") }
			],
			"default": "Mins",
			"reqd": 1
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"get_query": function() {
				var company = frappe.query_report_filters_by_name.company.get_value();
				var show_active = frappe.query_report_filters_by_name.show_active.get_value();
				var filters_list = {'company': company};
				if (show_active){
					filters_list['is_active'] = '1';
				}
				return{filters: filters_list};
			},
		},
		{
			"fieldname": "show_break",
			"label": __("Show Break Time"),
			"fieldtype": "Check",
		},
		{
			"fieldname": "show_active",
			"label": __("Show Active"),
			"fieldtype": "Check",
			"default": "1",
		},
		{
			"fieldname": "ignore_payroll_schedule",
			"label": __("Ignore Payroll Schedule Policy"),
			"fieldtype": "Check",
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
	]
};
