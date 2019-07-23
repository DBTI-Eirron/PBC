// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('appraisal', 'company', 'subsidiary');
cur_frm.add_fetch('appraisal', 'appraisee', 'employee');
cur_frm.add_fetch('appraisal', 'total_score', 'pa_rating');
cur_frm.add_fetch('appraisal', 'target_setting_period', 'pa_period');
cur_frm.add_fetch('appraisal', 'appraisee_name', 'employee_name');
cur_frm.add_fetch('appraisal', 'department', 'department');
frappe.ui.form.on('Performance Improvement Plan', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1){
			frappe.call({
				method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
				args:{
					doctype_name: "Performance Improvement Plan"
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

	evaluation: function(frm) {
		frm.trigger("get_appraisal");
	},

	get_appraisal: function(frm) {
		frm.doc.items = null;
		return frappe.call({
			method: "get_appraisal",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("items");
				frm.refresh_fields();
			}
		});
	},

});

cur_frm.fields_dict['appraisal'].get_query = function(doc) {
	return {
		filters: {
			"docstatus": 1,		
			"appraisee": doc.employee
		}
	}
}