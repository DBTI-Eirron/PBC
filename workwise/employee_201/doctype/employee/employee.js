// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Employee', {

	onload: function(frm){
		cur_frm.set_query("department", function() {
			return {
				"filters": {
					"is_group": 0,
				}
			};
		});
	},

	refresh: function(frm) {
		frappe.dynamic_link = {doc: frm.doc, fieldname: 'name', doctype: 'Employee'}
		frm.toggle_display(['address_html','contact_html'], !frm.doc.__islocal);
		if(!frm.doc.__islocal) {
			frappe.contacts.render_address_and_contact(frm);
		} else {
			frappe.contacts.clear_address_and_contact(frm);
		}
	}
	
});
