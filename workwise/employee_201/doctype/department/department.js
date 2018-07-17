// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Department', {
	refresh: function(frm) {
		frm.trigger("set_root_readonly");
		frm.add_custom_button(__("Department Tree"), function() {
			frappe.set_route("Tree", "Department");
		});
	},

	set_root_readonly: function(frm) {
		frm.set_intro("");
		if(frm.doc.is_root) {
			frm.set_read_only();
			frm.set_intro(__("This is a root Department and cannot be edited."), true);
		}
	},
});