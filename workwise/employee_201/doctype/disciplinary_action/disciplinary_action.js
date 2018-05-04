// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.provide("workwise.disciplinary_action");

frappe.ui.form.on('Disciplinary Action', {
	refresh: function(frm) {
		if((!frm.doc.__islocal) && (frm.doc.sanction=='Termination') && (frm.doc.docstatus===1)){
			frm.add_custom_button(__('Make Movement'),
				function() {
					workwise.disciplinary_action.make_movement(frm)
				}
			);
		}
	},

	suspended_from: function(frm){
		frm.trigger("calc_suspension_days"); 
	},

	suspended_to: function(frm){
		frm.trigger("calc_suspension_days"); 
	},

	calc_suspension_days: function(frm) {
		if( frm.doc.suspended_from && frm.doc.suspended_to ) {
			return frappe.call({
				method: "workwise.hr.doctype.disciplinary_action.disciplinary_action.calc_days",
				args: {
					suspended_from: frm.doc.suspended_from,
					suspended_to: frm.doc.suspended_to,
				},
				callback: function(r) {
					if (!r.exc && r.message) {
						frm.set_value("suspension", r.message.suspension_days);
					}
				}
			});	
		}
	},
});

workwise.disciplinary_action.make_movement = function(frm) {
	frappe.model.open_mapped_doc({
		method: "workwise.hr.doctype.disciplinary_action.disciplinary_action.make_movement",
		frm: frm
	});
};