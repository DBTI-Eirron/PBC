// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');
cur_frm.add_fetch('employee','department','department');

frappe.ui.form.on('Undertime Application', {
	onload: function(frm) {
		cur_frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});
	},

	refresh: function(frm) {

	},
});
