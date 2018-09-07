// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('BIR2316', {
	onload: function(frm) {
		
	},

	refresh: function(frm) {
		cur_frm.toggle_display('employee_info', false);
		cur_frm.toggle_display('wife_exemption_claim', false);
		var host_link = window.location.hostname+":8080";
		if(frm.doc.docstatus == 1){
			frm.add_custom_button(__('Print BIR2316'),
			function() {
				window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2FBIR2316&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
			});
		}
	},

	payroll_year: function(frm) {
		frm.trigger("load_dates");
	},

	load_dates: function(frm) {
		if(frm.doc.payroll_year) {
			return frappe.call({
				method: "load_dates",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	setup: function(frm) {
		frm.add_fetch("employee", "full_name", "employee_name");
	},

	get_info: function(frm) {
		if(frm.doc.employee && frm.doc.from_date && frm.doc.to_date){
			return frappe.call({
				method: "get_info",
				doc: frm.doc,
				callback: function(r) {
					cur_frm.toggle_display('employee_info', true);
					cur_frm.toggle_display('wife_exemption_claim', true);
					frm.refresh_fields();
				}
			});
		} 
	},
});
