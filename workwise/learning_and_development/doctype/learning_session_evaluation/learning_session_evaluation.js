// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');

frappe.ui.form.on('Learning Session Evaluation', {
	refresh: function(frm) {
		if (frm.doc.docstatus == 1){
			frappe.call({
				method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
				args:{
					doctype_name: "Learning Session Evaluation"
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

		hideTheButtonWrapper = $('*[data-fieldname="evaluation_table"]');
		hideTheButtonWrapper.find('.grid-add-row').hide();
		//hideTheButtonWrapper.find('.grid-remove-row').hide();
		frm.get_field("evaluation_table").grid.only_sortable()
	},

	learning_event: function(frm) {
		frappe.call({
			method: "get_evaluation_items",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
});
