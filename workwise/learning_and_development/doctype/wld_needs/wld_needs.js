// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('WLD Needs', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1) {
			frappe.call({
				method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
				args:{
					doctype_name: "WLD Needs"
				},
				callback: function(r) {
					r.message.forEach(function(item) {
						cur_frm.add_custom_button(__(item.form_label),
						function() {
							window.open("http://"+ item.form_ip +":"+ item.form_port +"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2F"+ item.form_folder +"&reportUnit=%2FReports%2F"+ item.form_name +"&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
						});
					});
				}
			});

			cur_frm.add_custom_button(__('Update Status'), cur_frm.cscript['Update Status'], __("Update"));
			cur_frm.page.set_inner_btn_group_as_primary(__("Update"));
		}
	},

	onload: function(frm){
		frm.set_query("department", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});

	},

});

cur_frm.cscript['Update Status'] = function() {
	frappe.model.open_mapped_doc({
		method: "workwise.learning_and_development.doctype.wld_needs.wld_needs.update_status",
		frm: cur_frm
	})
}
