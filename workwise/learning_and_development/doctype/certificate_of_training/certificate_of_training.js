// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Certificate of Training', {
	onload: function(frm) {

	},

	refresh: function(frm) {
		if (frm.doc.docstatus == 1){
			frappe.call({
				method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
				args:{
					doctype_name: "Certificate of Training"
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
	},
});