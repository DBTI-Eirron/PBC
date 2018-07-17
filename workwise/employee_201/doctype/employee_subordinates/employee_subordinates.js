// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee', 'full_name', 'employee_name')
cur_frm.add_fetch('subordinate', 'full_name', 'subordinate_name')

frappe.ui.form.on('Employee Subordinates', {
	refresh: function(frm) {

	},

	filter_type: function(frm) {
		frm.set_value("filter_value",null)
	},

	filter_add: function(frm) {
		if(frm.doc.filter_value && frm.doc.filter_type) {
			return frappe.call({
				method: "filter_add",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	filter_reset: function(frm) {	
		return frappe.call({
			method: "filter_reset",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});	
	},

});
