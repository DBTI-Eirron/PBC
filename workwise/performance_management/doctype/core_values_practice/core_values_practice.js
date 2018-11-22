// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('appraisee', 'full_name', 'appraisee_name');
cur_frm.add_fetch('appraisee', 'department', 'department');
cur_frm.add_fetch('appraisee', 'position_title', 'position');
frappe.ui.form.on('Core Values Practice', {
	onload: function(frm) {
		frm.trigger("display_settings_value");
	},
	refresh: function(frm) {
		frappe.call({
			method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
			args:{
				doctype_name: "Core Values Practice"
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
	},
	display_settings_value: function(frm){
		if(frm.doc.description == null  && frm.doc.values_indicator == null){
			return frappe.call({
				method: "display_settings_value",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("description");
					frm.refresh_field("values_indicator");
					frm.refresh_fields();
				}
			});
		}
	},
});
