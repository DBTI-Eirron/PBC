// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Disciplinary Action', {
	refresh: function(frm) {
		if((!frm.doc.__islocal) && (frm.doc.sanction=='Termination') && (frm.doc.docstatus===1)){
			frm.add_custom_button(__('Make Movement'), function(){
				var route_doc = frappe.model.get_new_doc('Employee Movement');
				route_doc.employee = frm.doc.employee;
				frappe.set_route('Form', 'Employee Movement', route_doc.name);
			});
		}
	},

	suspended_from: function(frm){
		frm.trigger("calc_suspension_days"); 
	},

	suspended_to: function(frm){
		frm.trigger("calc_suspension_days"); 
	},

	ex_holiday: function(frm){
		frm.trigger("calc_suspension_days"); 
	},
	ex_restday: function(frm){
		frm.trigger("calc_suspension_days"); 
	},
	calc_suspension_days: function(frm) {
		if( frm.doc.suspended_from && frm.doc.suspended_to ) {
			frappe.call({
				method: "calc_days",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		}
	},
});

//workwise.disciplinary_action.make_movement = function(frm) {
//	frappe.model.open_mapped_doc({
//		method: "workwise.employee_201.doctype.disciplinary_action.disciplinary_action.make_movement",
//		frm: frm
//	});
//};