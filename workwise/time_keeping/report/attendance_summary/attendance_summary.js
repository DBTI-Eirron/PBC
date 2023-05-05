frappe.query_reports["Attendance Summary"] = {
	"filters": [
		{
			"fieldname": "payroll_period",
			"label": __("Payroll Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
			"reqd": 1,
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"reqd": 1,
			"on_change": function(query_report) {
				var employee = query_report.get_values().employee;
				if (!employee) {
					return;
				}
				frappe.model.with_doc("Employee", employee, function(r) {
					var emp = frappe.model.get_doc("Employee", employee);
					frappe.query_report_filters_by_name.employee_name.set_input(emp.full_name);
					query_report.trigger_refresh();
				});
			}
		},
		{
			"fieldname": "employee_name",
			"label": __("Employee Name"),
			"fieldtype": "Data",
			"read_only": 1
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
			"fieldname": "show_break",
			"label": __("Show Break Time"),
			"fieldtype": "Check",
		},
		{
			"fieldname": "show_adjusted",
			"label": __("Show Adjusted"),
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
	]/*,
	"formatter": function(row, cell, value, columnDef, dataContext, default_formatter) {
		if (columnDef.df.fieldname=="account") {
			value = dataContext.account_name;

			columnDef.df.link_onclick = "frappe.query_reports['Trial Balance'].open_general_ledger(" + JSON.stringify(dataContext) + ")";
			columnDef.df.is_tree = true;
		}

		value = default_formatter(row, cell, value, columnDef, dataContext);

		if (!dataContext.account) {
			var $value = $(value).css("font-weight", "bold");
			if (dataContext.warn_if_negative && dataContext[columnDef.df.fieldname] < 0) {
				$value.addClass("text-danger");
			}

			value = $value.wrap("<p></p>").parent().html();
		}

		return value;
	},
	"open_general_ledger": function(data) {
		if (!data.account) return;

		frappe.route_options = {
			"account": data.account,
			"company": frappe.query_report.filters_by_name.company.get_value(),
			"from_date": frappe.query_report.filters_by_name.from_date.get_value(),
			"to_date": frappe.query_report.filters_by_name.to_date.get_value(),
		};
		frappe.set_route("query-report", "General Ledger");
	},
	"tree": true,
	"name_field": "account",
	"parent_field": "parent_account",
	"initial_depth": 100*/
};

//Get Current Period
frappe.call({
	method: "workwise.time_keeping.report.attendance_summary.attendance_summary.get_current_period",
	callback: function(r) {
		frappe.query_reports["Attendance Summary"]["filters"][0]["default"] = r.message
	}
});