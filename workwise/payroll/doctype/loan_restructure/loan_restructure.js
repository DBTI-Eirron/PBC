// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt

cur_frm.add_fetch('employee','sensitivity','sensitivity');

frappe.ui.form.on('Loan Restructure', {
	refresh: function(frm) {

	},

	setup: function(frm) {
		frm.add_fetch('employee','sensitivity','sensitivity');
	},
});
