// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Interview', {
	refresh: function(frm) {

	},

	setup: function(frm) {
		frm.add_fetch("interviewer", "full_name", "interviewer_name");
	},	
});