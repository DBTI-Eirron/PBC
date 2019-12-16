// Copyright (c) 2016, HDI Systech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["PagIbig Loan Report"] = {
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
		{
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
		{
			"fieldname": "include_header",
			"label": __("Include Header"),
			"fieldtype": "Check",
		},
	],
	
	//onload: function(report) {
	//	var host_link = window.location.hostname+":8080";
	//	report.page.add_inner_button(__("Export as Excel"), function() {
	//		var from_date = frappe.query_report_filters_by_name.from_date.get_value();
	//		var to_date = frappe.query_report_filters_by_name.to_date.get_value();
	//		var company = frappe.query_report_filters_by_name.company.get_value();		
	//		window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2Fpagibig_loan_report&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=xlsx&company="+company+"&from_date="+from_date+"&to_date="+to_date+"");
	//	});
	//},
}
