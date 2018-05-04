// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');
cur_frm.add_fetch('new_shift','time_in','new_time_in');
cur_frm.add_fetch('new_shift','time_out','new_time_out');

frappe.ui.form.on('Change Schedule Application', {
	refresh: function(frm) {

	},

	employee: function(frm) {
		frm.trigger("get_work_shift");
	},

	target_date: function(frm) {
		frm.trigger("get_work_shift");
	},

	get_work_shift: function(frm) {
		if( frm.doc.employee && frm.doc.target_date) {
			return frappe.call({
				method: "get_shift",
				doc: frm.doc,
				callback: function(r) {
					if (!r.exc && r.message) {
						frm.set_value("old_shift", r.message.old_shift);
					}
				}
			});	
		}
	},
	
});
