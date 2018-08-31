// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('My Payslip', {
	onload: function(frm){

	},

	refresh: function(frm){
		var host_link = window.location.hostname+":8080";
		cur_frm.toggle_display('basic_section',false);
		cur_frm.toggle_display('entries_section',false);
		cur_frm.toggle_display('totals_section',false);
		frm.pass_dialog = new frappe.ui.Dialog({
			title: __("Enter Password"),
			fields: [
				{fieldname:'payslip_password', fieldtype:'Password', label: __('Password')}
			]
		});
		frm.pass_dialog.set_primary_action(__("Login"), function() {
			var filters = frm.pass_dialog.get_values();
			frappe.call({
				method: "check_password",
				args:{
					filters: filters.payslip_password
				},
				doc: frm.doc,
				callback: function(r) {
					if (r.message == false){
						frappe.set_route("List", "My Payslip");
					} else {
						cur_frm.toggle_display('basic_section', true);
						cur_frm.toggle_display('entries_section', true);
						cur_frm.toggle_display('totals_section', true);		
					}
					frm.pass_dialog.hide()
					frm.add_custom_button(__('Print Payslip'),
						function() {
							window.open("http://192.168.1.169:8080/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2FPayslip2&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
						});
				}
			});
		});
		frm.pass_dialog.show();
		
		cur_frm.set_query("payroll_period", function() {
			return {
				"filters": {
					"status": "Closed",
					"company": frm.doc.company,
				}
			};
		});
	},

});
