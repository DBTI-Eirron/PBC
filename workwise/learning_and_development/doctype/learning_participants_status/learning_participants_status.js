// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Learning Participants Status', {
	refresh: function(frm) {
		frappe.call({
			method: "get_program_session",
			doc: frm.doc,
			callback: function(r) {
				frm.set_df_property('program_session', 'options', r.message);
				frm.refresh_field('program_session');
			}
		});
	},

	program_session: function(frm) {
		frappe.call({
			method: "get_attendance_data",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field('participants');
			}
		});
	},

	on_submit: function(frm) {
		frappe.set_route('Form', 'Learning Event', frm.doc.learning_event);
	},
});
