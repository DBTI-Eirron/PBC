// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee', 'full_name', 'employee_name')
cur_frm.add_fetch('subordinate', 'full_name', 'subordinate_name')

frappe.ui.form.on('Employee Subordinates', {
	refresh: function(frm) {

	}
});
