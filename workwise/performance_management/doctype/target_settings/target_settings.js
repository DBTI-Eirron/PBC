// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt
this.frm.get_field("target_employees").grid.cannot_add_rows = true;
frappe.ui.form.on('Target Settings', {
	onload: function(frm) { 

	},
	add: function(frm) {
		frappe.call({
			method: "get_employees",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	clear: function(frm) {
		frm.doc.target_employees = null
		frm.refresh_fields()
	},
});
