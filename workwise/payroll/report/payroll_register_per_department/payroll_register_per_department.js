frappe.query_reports["Payroll Register Per Department"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},
		{
			"fieldname": "payroll_period",
			"label": __("Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
			"get_query": function() {
				var company = frappe.query_report_filters_by_name.company.get_value();
				return{
					filters: {
						'company': company
					}
				};
			},
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
						'company': company
					}
				};
			}
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"reqd": 0
		},
				{
			"fieldname": "hide_zero",
			"label": __("Hide zero value"),
			"fieldtype": "Check",
		},
	]
};
