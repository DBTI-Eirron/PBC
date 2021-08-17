// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');
cur_frm.add_fetch('employee','department','department');

frappe.ui.form.on('Excuse Tardiness Application', {
	onload: function(frm) {
		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today());
		}

		cur_frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});
	},
	
	date: function(frm) {
		if(frm.doc.employee && frm.doc.date) {
			return frappe.call({
				method: "load_timecard",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	refresh: function(frm) {

	},
});
