// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Employee', {

	onload: function(frm){

	},

	refresh: function(frm) {
		frappe.dynamic_link = {doc: frm.doc, fieldname: 'name', doctype: 'Employee'}
		frm.toggle_display(['address_html','contact_html'], !frm.doc.__islocal);
		if(!frm.doc.__islocal) {
			frappe.contacts.render_address_and_contact(frm);
		} else {
			frappe.contacts.clear_address_and_contact(frm);
		}
		
		frappe.call({
			method: "get_user_sensitivity_level",
			doc: frm.doc,
			callback: function(r) {
				if (r.message == "access_denied"){
					cur_frm.toggle_display('section_break_29',false);
					//cur_frm.toggle_display('section_break_16',false);
				}
				else{
					cur_frm.toggle_display('section_break_29',true);
					//cur_frm.toggle_display('section_break_16',true);
				}
			}
		});

		frappe.call({
			method: "get_age_and_service_years",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});

		cur_frm.set_query("default_schedule", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});

		cur_frm.set_query("reports_to", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});

		cur_frm.set_query("department", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});

		cur_frm.set_query("approver", "approvers", function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return{
				filters: [
					['Employee', 'is_active', '=', 1]
				]
			}
		});
	}
	
});