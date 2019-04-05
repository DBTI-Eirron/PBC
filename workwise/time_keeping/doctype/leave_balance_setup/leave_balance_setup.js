// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Balance Setup', {
	refresh: function(frm) {

	},

	setup: function(frm) {
		frm.add_fetch("employee", "full_name", "employee_name");
	},
});
