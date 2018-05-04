// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

cur_frm.add_fetch('employee', 'company', 'company');
cur_frm.add_fetch('employee', 'full_name', 'employee_name');
cur_frm.add_fetch('appraisal_dates', 'start_date', 'start_date');
cur_frm.add_fetch('appraisal_dates', 'end_date', 'end_date');

frappe.ui.form.on('Appraisal', {
	refresh: function(frm) {
	
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

	appraisal_template: function(frm) {
		frm.trigger("get_appraisal_template_goal");
	},

	get_appraisal_template_goal: function(frm) {
		if(frm.doc.appraisal_template) {
			return frappe.call({
				method: "get_appraisal_template_goal",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("appraisal_goal");
					frm.refresh_fields();
				}
			});
		} 
	},
});	
