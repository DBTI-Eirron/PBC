// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Type', {
	refresh: function(frm) {

	},

	male_only: function(frm) {
		frm.set_value("female_only", 0);
	},

	female_only: function(frm) {
		frm.set_value("male_only", 0);
	},
});
