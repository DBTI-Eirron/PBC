// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','full_name');
cur_frm.add_fetch('employee','company','company');
cur_frm.add_fetch('employee','department','department');

frappe.ui.form.on('Change Request Application', {
	refresh: function(frm) {
		cur_frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});
	},

	onload: function(frm) {
		//if (!frm.doc.posting_date && frm.doc.docstatus < 1) {
		//	frm.set_value("date_submitted", get_today());
		//}
	},
	
});

frappe.ui.form.on("Change Request Application Table", "item", function(frm, cdt, cdn) {
	return frappe.call({
		method: "get_request",
		doc: frm.doc,
		callback: function(r) {
			frm.refresh_field("change_request");
		}
	});
});