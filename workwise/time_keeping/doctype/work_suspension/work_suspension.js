// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Work Suspension', {
	refresh: function(frm) {
		
	},

	company: function(frm) {
		frm.doc.apply_to = null
		frappe.call({
			method: "get_employees",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	
	location: function(frm) {
		frm.doc.apply_to = null
		frappe.call({
			method: "get_employees",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

	department: function(frm) {
		frm.doc.apply_to = null
		frappe.call({
			method: "get_employees",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

});
