// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee', 'date_hired', 'from_date');
cur_frm.add_fetch('employee', 'full_name', 'employee_name');
cur_frm.add_fetch('certified_by', 'full_name', 'certified_name');
frappe.ui.form.on('Certificate of Employment', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1){
			frappe.call({
				method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
				args:{
					doctype_name: "Certificate of Employment"
				},
				callback: function(r) {
					r.message.forEach(function(item) {
						frm.add_custom_button(__(item.form_label),
						function() {
							window.open("http://"+ item.form_ip +":"+ item.form_port +"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2F"+ item.form_folder +"&reportUnit=%2FReports%2F"+ item.form_name +"&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output="+item.output+"&filter1="+frm.doc.name+"");
						});
					});
				}
			});
		}
	},
	employee: function(frm) {
		return frappe.call({
			method: "get_to_date",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	}
});
