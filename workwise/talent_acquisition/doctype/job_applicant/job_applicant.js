// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Job Applicant', {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			if (frm.doc.docstatus == 1) {
				frm.add_custom_button(__("Make Schedules and Assessment"), function() {
					frappe.route_options = {
						"applicant": frm.doc.name,
						"applicant_name": frm.doc.applicant_name,
						"apply_for": frm.doc.apply_for,
					};
					frappe.new_doc("Schedules and Assessment");
				}, __("Make"));
				cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
			}
		}
		frappe.call({
			method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
			args:{
				doctype_name: "Job Applicant"
			},
			callback: function(r) {
				if (r.message){
					r.message.forEach(function(item) {
						frm.add_custom_button(__(item.form_label),
						function() {
							window.open("http://"+ item.form_ip +":"+ item.form_port +"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2F"+ item.form_folder +"&reportUnit=%2FReports%2F"+ item.form_name +"&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
						});
					});
				}
			}
		});
	},
});
