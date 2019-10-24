// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('WLD Needs Status', {
	refresh: function(frm) {

	},

	on_submit: function(frm) {
		frappe.set_route('Form', 'WLD Needs', frm.doc.wld_needs_id);
	},
});