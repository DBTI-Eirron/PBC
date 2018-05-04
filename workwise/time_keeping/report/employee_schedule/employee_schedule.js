frappe.query_reports["Employee Schedule"] = {
	"filters": [
		{
			"fieldname": "payroll_period",
			"label": __("Payroll Period"),
			"fieldtype": "Link",
			"options": "Payroll Period",
			"reqd": 1
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"reqd": 1
		}
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
