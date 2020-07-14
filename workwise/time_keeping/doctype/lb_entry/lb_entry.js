// Copyright (c) 2019, OSI and contributors
// For license information, please see license.txt

cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');
cur_frm.add_fetch('leave_type','deduct_to','deduct_credits_to');

frappe.ui.form.on('LB Entry', {
	refresh: function(frm) {

	},
	
	onload: function(frm) {
		cur_frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});
	},
});
