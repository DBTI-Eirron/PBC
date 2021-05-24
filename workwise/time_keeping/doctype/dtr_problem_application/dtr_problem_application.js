 // Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');

frappe.ui.form.on('DTR Problem Application', {
	onload: function(frm) {
		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today());
		}
	},		

	refresh: function(frm) {
		cur_frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});

		frappe.call({
			method: "enable_isprevious",
			doc: frm.doc,
			callback: function(r) {
				frm.toggle_display("is_previous", r.message);
			}
		});
	},

});

