var today = new Date();
frappe.query_reports["BIR1601-C per Company"] = {
	"filters": [
		{
			"fieldname": "year",
			"label": __("Year"),
			"fieldtype": "Link",
			"options": "Payroll Year",
			"default": today.getFullYear(),
			"reqd": 1
		},
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"options": [
				{ "value": "January", "label": __("January") },
				{ "value": "February", "label": __("February") },
				{ "value": "March", "label": __("March") },
				{ "value": "April", "label": __("April") },
				{ "value": "May", "label": __("May") },
				{ "value": "June", "label": __("June") },
				{ "value": "July", "label": __("July") },
				{ "value": "August", "label": __("August") },
				{ "value": "September", "label": __("September") },
				{ "value": "October", "label": __("October") },
				{ "value": "November", "label": __("November") },
				{ "value": "December", "label": __("December") },
			],
			"default": today.getMonth(),
			"reqd": 1
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
			"fieldname": "hide_zero",
			"label": __("Hide zero value"),
			"fieldtype": "Check",
		},
	],

	// onload: function(report) {
	// 	frappe.call({
	// 		method: "workwise.setup.doctype.jasper_form.jasper_form.get_server_info",
	// 		callback: function(r) {
	// 			if(r.message){
	// 				var host_link = ""+r.message.jasper_ip+":"+r.message.jasper_port+"";
	// 				report.page.add_inner_button(__("Print BIR1601-C"), function() {
	// 					var company = frappe.query_report_filters_by_name.company.get_value();
	// 					var year = frappe.query_report_filters_by_name.year.get_value();
	// 					var month = frappe.query_report_filters_by_name.month.get_value();
	// 					var from_date = year + "-" + month + "-1";
	// 					var to_date = year + "-" + ((parseInt(month,10))+1) + "-1";
	// 					window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2FBIR1601&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&company="+company+"&from_date="+from_date+"&to_date="+to_date+"");
	// 				});				
	// 			}
	// 		}
	// 	});		
	// },
};
