frappe.query_reports["SSS Premium Contribution"] = {
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
		{
			"fieldname": "period_group",
			"label": __("Period Group"),
			"fieldtype": "Link",
			"options": "Period Group",
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
					var session_user = r.message.session_user;

					report.page.add_inner_button(__("Print SSS Certificate"), function() {
						var from_date = frappe.query_report_filters_by_name.from_date.get_value();
						var to_date = frappe.query_report_filters_by_name.to_date.get_value();
						var company = frappe.query_report_filters_by_name.company.get_value();
						var group = frappe.query_report_filters_by_name.period_group.get_value();
						window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2Fsss_certificate&standAlone=true&j_username="+username+"&j_password="+password+"&output=pdf&company="+company+"&user="+session_user+"&group="+group+"&from_date="+from_date+"&to_date="+to_date);
					});

					report.page.add_inner_button(__("Print SSS Premium Contribution"), function() {
						var from_date = frappe.query_report_filters_by_name.from_date.get_value();
						var to_date = frappe.query_report_filters_by_name.to_date.get_value();
						var company = frappe.query_report_filters_by_name.company.get_value();
						var group = frappe.query_report_filters_by_name.period_group.get_value();
						window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2Fsss_premium_contribution&standAlone=true&j_username="+username+"&j_password="+password+"&output=pdf&company="+company+"&user="+session_user+"&group="+group+"&from_date="+from_date+"&to_date="+to_date);
					});

					report.page.add_inner_button(__("Print R-3 Form"), function() {
						var from_date = frappe.query_report_filters_by_name.from_date.get_value();
						var to_date = frappe.query_report_filters_by_name.to_date.get_value();
						var company = frappe.query_report_filters_by_name.company.get_value();	
						var group = frappe.query_report_filters_by_name.period_group.get_value();
						window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2Fr3_form&standAlone=true&j_username="+username+"&j_password="+password+"&output=pdf&company="+company+"&user="+session_user+"&group="+group+"&from_date="+from_date+"&to_date="+to_date);
					});					
				}
			}
		});
	},
};