// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','full_name');
cur_frm.add_fetch('employee','company','company');
cur_frm.add_fetch('employee','department','department');

frappe.ui.form.on('Leave Application', {
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

	employee: function(frm) {
		frm.trigger("get_leaves_balances");
	},

	leave_type: function(frm) {
		frm.trigger("get_leaves_balances");
	},

	from_date: function(frm) {
		frm.trigger("get_leaves_balances");
	},

	to_date: function(frm) {
		frm.trigger("get_leaves_balances");
	},

	get_leaves_balances: function(frm) {
		if(frm.doc.employee && frm.doc.leave_type && frm.doc.from_date && frm.doc.to_date) {
			return frappe.call({
				method: "get_leaves_balances",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("leave_application_table");
				}
			});
		} 
	},
	
});
