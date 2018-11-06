// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('appraisee', 'date_hired', 'date_joined');
cur_frm.add_fetch('appraisee', 'full_name', 'appraisee_fullname');
frappe.ui.form.on('Appraisal', {
	refresh: function(frm) {
	
	},

	onload: function(frm) {
		frm.trigger("set_header");
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

	due_date: function(frm) {
		if (frm.doc.due_date < frappe.datetime.get_today()){
			frm.trigger("get_behind_target");
		}else{
			frm.trigger("get_not_behind_target");
		}
	},

	get_behind_target: function(frm) {
		frm.set_value("status", 'Behind Target');;
	},

	get_not_behind_target: function(frm) {
		frm.set_value("status", 'Draft');;
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