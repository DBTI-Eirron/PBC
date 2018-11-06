// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.provide("workwise.offer_letter");

frappe.ui.form.on('Offer Letter', {
	refresh: function(frm) {
		if((!frm.doc.__islocal) && (frm.doc.status=='Accepted') && (frm.doc.docstatus===1)  && frm.doc.signed_contract ){
			frm.add_custom_button(__('Make Employee'),
				function() {
					workwise.offer_letter.make_employee(frm)
				}
			);
		}
	},

	setup: function(frm) {
		frm.add_fetch("representative", "full_name", "representative_name");
		frm.add_fetch("representative", "position_title", "representative_position");
	},		
});

workwise.offer_letter.make_employee = function(frm) {
	frappe.model.open_mapped_doc({
		method: "workwise.talent_acquisition.doctype.offer_letter.offer_letter.make_employee",
		frm: frm
	});
};