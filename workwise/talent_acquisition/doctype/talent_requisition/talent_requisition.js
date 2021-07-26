// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Talent Requisition', {
	refresh: function(frm) {
		frappe.call({
			method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
			args:{
				doctype_name: "Talent Requisition"
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
	}
});
