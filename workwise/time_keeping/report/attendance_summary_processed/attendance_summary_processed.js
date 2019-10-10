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
			"fieldtype": "Data",
			"options": [
				{ "value": "Hrs	", "label": __("Hrs") }
			],
			"default": "Hrs",
			"reqd": 1
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"get_query": function() {
				var company = frappe.query_report_filters_by_name.company.get_value();
				return{
					filters: {
						'company': company,
					}
				};
			},
		},
		{
			"fieldname": "show_break",
			"label": __("Show Break Time"),
			"fieldtype": "Check",
		},
		{
			"fieldname": "ignore_payroll_schedule",
			"label": __("Ignore Payroll Schedule Policy"),
			"fieldtype": "Check",
		},
	]
};
