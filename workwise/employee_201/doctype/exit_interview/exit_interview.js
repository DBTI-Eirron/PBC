// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','full_name');
cur_frm.add_fetch('employee','position_title','position_title');

frappe.provide("workwise.exit_interview");

frappe.ui.form.on('Exit Interview', {
	refresh: function(frm) {
		if((!frm.doc.__islocal) && (frm.doc.docstatus===1)){
			frm.add_custom_button(__('Make Movement'),
				function() {
					workwise.exit_interview.make_movement(frm)
				}
			);
		}
	},
	onload: function(frm) {
		if (frm.doc.__islocal){
			frm.set_value("employee", "");
		}
	},
});

workwise.exit_interview.make_movement = function(frm) {
	frappe.model.open_mapped_doc({
		method: "workwise.hr.doctype.exit_interview.exit_interview.make_movement",
		frm: frm
	});
};