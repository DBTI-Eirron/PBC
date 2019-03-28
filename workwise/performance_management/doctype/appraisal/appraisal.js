// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('appraisee', 'date_hired', 'date_joined');
cur_frm.add_fetch('appraisee', 'full_name', 'appraisee_name');
cur_frm.add_fetch('appraisee', 'department', 'department');
cur_frm.add_fetch('appraisee', 'company', 'company');
cur_frm.add_fetch('appraisee', 'position_title', 'job_title');
frappe.ui.form.on('Appraisal', {
	refresh: function(frm) {
		// if(frm.doc.docstatus == 1){
		// 	frappe.call({
		// 		method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
		// 		args:{
		// 			doctype_name: "Appraisal"
		// 		},
		// 		callback: function(r) {
		// 			r.message.forEach(function(item) {
		// 				frm.add_custom_button(__(item.form_label),
		// 				function() {
		// 					window.open("http://"+ item.form_ip +":"+ item.form_port +"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2F"+ item.form_folder +"&reportUnit=%2FReports%2F"+ item.form_name +"&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
		// 				});
		// 			});
		// 		}
		// 	});
		// }
	},

	onload: function(frm) {
		if (!frm.doc.status) {
			frm.set_value("status", 'Draft');
		}
		if (!frm.doc.date_created) {
			frm.set_value("date_created", frappe.datetime.get_today());
		}
		if (frm.doc.status != 'Submitted/Completed') {
			if (frm.doc.due_date < frappe.datetime.get_today()) {
				frm.set_value("status", 'Behind Target');
			}
		}
	},

	get_behind_target: function(frm) {
		frm.set_value("status", 'Behind Target');
	},

	get_not_behind_target: function(frm) {
		frm.set_value("status", 'Draft');
	},

	target_setting: function(frm) {
		frm.trigger("get_performance_planning");
	},


	get_performance_planning: function(frm) {
		if(frm.doc.target_setting) {
			frm.doc.appraisal_goal = null;
			return frappe.call({
				method: "get_performance_planning",
				doc: frm.doc,
				callback: function(r) {
    				frm.set_df_property("appraisee", "read_only", r.message == "Individual");
					frm.refresh_field("appraisal_goal");
					frm.refresh_fields();
				}
			});
		} 
	},
	set_header: function(frm) {
		return frappe.call({
			method: "set_header",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("header");
				frm.refresh_fields();
			}
		});
	},
});	

cur_frm.fields_dict['target_setting'].get_query = function(doc) {
	return {
		filters: {
			"docstatus": 1
		}
	}
}

frappe.ui.form.on("Appraisal", "onload", function(frm) {
    cur_frm.set_query("appraisee", function() {
        return {
            "filters": {
                "department": frm.doc.department
            }
        };
    });
});

frappe.ui.form.on("Appraisal Goal", "score", function(frm, cdt, cdn) {
   var item = locals[cdt][cdn];
   var score_earned = (item.weightage / 100) * item.score;
   frappe.model.set_value(cdt, cdn, 'score_earned',score_earned)
});