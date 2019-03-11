// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('appraisee','company','company');
cur_frm.add_fetch('appraisee','full_name','appraisee_name');
cur_frm.add_fetch('appraisee','position_title','job_title');
cur_frm.add_fetch('appraisee','department','department');
cur_frm.add_fetch('appraisee','date_hired','date_joined');
frappe.ui.form.on('Target Setting', {
	onload: function(frm) { 
	},
	refresh: function(frm) {
		if (frm.doc.type == "Individual" && frm.doc.docstatus == 1){
			frappe.call({
				method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
				args:{
					doctype_name: "Target Setting"
				},
				callback: function(r) {
					r.message.forEach(function(item) {
						frm.add_custom_button(__(item.form_label),
						function() {
							window.open("http://"+ item.form_ip +":"+ item.form_port +"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2F"+ item.form_folder +"&reportUnit=%2FReports%2F"+ item.form_name +"&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
						});
					});
				}
			});
		}
		if(frm.doc.key_result_area != null){
			return frappe.call({
				method: "change_key_indicator",
				doc: frm.doc,
				callback: function(r) {
					console.log(r.message)
					// frm.refresh_field("timelogs_override");
					frappe.meta.get_docfield('Performance Planning KI', 'key_result_area', cur_frm.doc.name).options = r.message;
					cur_frm.refresh_field('key_result_area');
				}
			});
		}
	},
	appraisee: function(frm) {
		frm.trigger("load_appraisee_info");
	},
	type: function(frm) {
		frm.trigger("get_type");
	},
	get_type: function(frm) {
		return frappe.call({
			method: "get_type",
			doc: frm.doc,
			callback: function(r) {
				frm.set_df_property("department", "read_only", r.message == "Individual");
				frm.refresh_fields();

			}
		});
	},
	load_appraisee_info: function(frm) {
		frm.doc.immediate_supervisor = null;
		frm.doc.immediate_supervisor_name = null;
		frm.doc.supervisor_job_title = null;
		if(frm.doc.appraisee) {
			return frappe.call({
				method: "load_appraisee_info",
				doc: frm.doc,
				callback: function(r) {
					// frm.refresh_field("timelogs_override");
					frm.refresh_fields();

				}
			});
		} 
	},
});
