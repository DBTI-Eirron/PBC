// Copyright (c) 2021, OSI and contributors
// For license information, please see license.txt

cur_frm.add_fetch('employee','full_name','full_name');
cur_frm.add_fetch('employee','company','company');

frappe.ui.form.on('Overused LB Entry', {
	refresh: function(frm) {

	}
});
