// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');
cur_frm.add_fetch('employee','department','department');

frappe.ui.form.on('Change Schedule Application', {
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

	from_date: function(frm) {
		if(frm.doc.from_date && frm.doc.to_date) {
			frm.trigger("get_dates");
		}
	},

	to_date: function(frm) {
		if(frm.doc.employee && frm.doc.from_date && frm.doc.to_date) {
			frm.trigger("get_dates");
		}
	},

	get_dates: function(frm) {
		if(frm.doc.from_date && frm.doc.to_date) {
			return frappe.call({
				method: "get_dates",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("change_list");
				}
			});
		} 
	},
	
});

frappe.ui.form.on("Change Schedule Application Table", "target_date", function(frm, cdt, cdn) {
	if(frm.doc.employee) {
		return frappe.call({
			method: "get_shift",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("change_list");
			}
		});
	}
});