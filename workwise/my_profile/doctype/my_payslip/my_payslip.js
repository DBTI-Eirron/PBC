// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('My Payslip', {
	onload: function(frm){

	},

	refresh: function(frm){
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
				}
			});
		});
		frm.pass_dialog.show();
		
		var host_link = window.location.hostname;
		var jasper_link = "178.128.220.33";

		if (frm.doc.docstatus===1 || frm.doc.docstatus===0) {
			frm.add_custom_button(__('Check Voucher'),
				function() {
					window.open("http://"+jasper_link+":8080/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2Freports&reportUnit=%2Freports%2Fje_check_voucher&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
				});
		}
		if (frm.doc.docstatus===1 || frm.doc.docstatus===0) {
			frm.add_custom_button(__('Print Check'),
				function() {
					window.open("http://"+jasper_link+":8080/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2Freports&reportUnit=%2Freports%2Fje_print_check&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
				});
		}
	},
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
