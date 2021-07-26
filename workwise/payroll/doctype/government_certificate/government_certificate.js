// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt
this.frm.get_field("employees").grid.cannot_add_rows = true;
cur_frm.add_fetch('certified_by', 'full_name', 'certified_name');
frappe.ui.form.on('Government Certificate', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1){
			frappe.call({
				method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
				args:{
					doctype_name: "Government Certificate"
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
	},
	add: function(frm) {
		frappe.call({
			method: "get_employees",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	clear: function(frm) {
		frm.doc.employees = null
		frm.refresh_fields()
	},

});
