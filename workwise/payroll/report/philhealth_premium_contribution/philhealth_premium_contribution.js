frappe.query_reports["PhilHealth Premium Contribution"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},	
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1
		},	
	],

	onload: function(report) {
		frappe.call({
			method: "workwise.setup.doctype.jasper_form.jasper_form.get_server_info",
			callback: function(r) {
				if(r.message){
					var host_link = ""+r.message.jasper_ip+":"+r.message.jasper_port+"";
					var username = r.message.jasper_user;
					var password = r.message.jasper_pass;

					report.page.add_inner_button(__("Print PHIC Certificate"), function() {
						var from_date = frappe.query_report_filters_by_name.from_date.get_value();
						var to_date = frappe.query_report_filters_by_name.to_date.get_value();
						var company = frappe.query_report_filters_by_name.company.get_value();
						window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2Fphic_certificate&standAlone=true&j_username="+username+"&j_password="+password+"&output=pdf&company="+company+"&from_date="+from_date+"&to_date="+to_date+"");
					});		
					//report.page.add_inner_button(__("Print PHIC Remittance Txt Form"), function() {
					//	var from_date = frappe.query_report_filters_by_name.from_date.get_value();
					//	var to_date = frappe.query_report_filters_by_name.to_date.get_value();
					//	var company = frappe.query_report_filters_by_name.company.get_value();
					//	window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2F_remittance&standAlone=true&j_username="+username+"&j_password="+password+"&output=pdf&company="+company+"&from_date="+from_date+"&to_date="+to_date+"");
					//});
					report.page.add_inner_button(__("Print RF-1"), function() {
						var from_date = frappe.query_report_filters_by_name.from_date.get_value();
						var to_date = frappe.query_report_filters_by_name.to_date.get_value();
						var company = frappe.query_report_filters_by_name.company.get_value();
						window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2Frf1_form&standAlone=true&j_username="+username+"&j_password="+password+"&output=pdf&company="+company+"&from_date="+from_date+"&to_date="+to_date+"");
					});
					report.page.add_inner_button(__("Print RF-1 Quarterly"), function() {
						var from_date = frappe.query_report_filters_by_name.from_date.get_value();
						var to_date = frappe.query_report_filters_by_name.to_date.get_value();
						var company = frappe.query_report_filters_by_name.company.get_value();
						window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2Frf1_quarterly_form&standAlone=true&j_username="+username+"&j_password="+password+"&output=pdf&company="+company+"&from_date="+from_date+"&to_date="+to_date+"");
					});				
				}
			}
		});		
	},/*,
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
