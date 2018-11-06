
var today = new Date();
frappe.query_reports["BIR1601-C"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1
		},	
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
				{ "value": "0", "label": __("January") },
				{ "value": "1", "label": __("February") },
				{ "value": "2", "label": __("March") },
				{ "value": "3", "label": __("April") },
				{ "value": "4", "label": __("May") },
				{ "value": "5", "label": __("June") },
				{ "value": "6", "label": __("July") },
				{ "value": "7", "label": __("August") },
				{ "value": "8", "label": __("September") },
				{ "value": "9", "label": __("October") },
				{ "value": "10", "label": __("November") },
				{ "value": "11", "label": __("December") },
			],
			"default": today.getMonth(),
			"reqd": 1
		},
	],

	onload: function(report) {
		frappe.call({
			method: "workwise.setup.doctype.jasper_form.jasper_form.get_server_info",
			callback: function(r) {
				if(r.message){
					var host_link = ""+r.message.jasper_ip+":"+r.message.jasper_port+"";
					report.page.add_inner_button(__("Print BIR1601-C"), function() {
						var company = frappe.query_report_filters_by_name.company.get_value();
						var year = frappe.query_report_filters_by_name.year.get_value();
						var month = frappe.query_report_filters_by_name.month.get_value();
						var from_date = year + "-" + month + "-1";
						var to_date = year + "-" + ((parseInt(month,10))+1) + "-1";
						window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2FBIR1601&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&company="+company+"&from_date="+from_date+"&to_date="+to_date+"");
					});				
				}
			}
		});		
	},
};
