// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.provide("workwise.offer_letter");

frappe.ui.form.on('Offer Letter', {
	refresh: function(frm) {
		if((!frm.doc.__islocal) && (frm.doc.status=='Accepted') && (frm.doc.docstatus===1)){
			frm.add_custom_button(__('Make Employee'),
				function() {
					workwise.offer_letter.make_employee(frm)
				}
			);
		}
	},

	job_applicant: function(frm){
 		if(frm.doc.job_applicant){
	 		return frappe.call({
				method: "workwise.hr.doctype.offer_letter.offer_letter.get_name",
				args: {
					source_name: "Applicant",
					source_value: frm.doc.job_applicant,
				},
				callback: function(r) {
					if (!r.exc && r.message) {
						frm.set_value("applicant_name", r.message.target_name);
						frm.set_value("designation", r.message.target_job_opening);
						frm.set_value("company", r.message.target_company);
						frm.set_value("location", r.message.target_location);
						
					}
				}
			});
		}
	},
});

workwise.offer_letter.make_employee = function(frm) {
	frappe.model.open_mapped_doc({
		method: "workwise.hr.doctype.offer_letter.offer_letter.make_employee",
		frm: frm
	});
};