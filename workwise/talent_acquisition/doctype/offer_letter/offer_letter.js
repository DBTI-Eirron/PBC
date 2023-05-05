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
		frappe.call({
			method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
			args:{
				doctype_name: "Offer Letter"
			},
			callback: function(r) {
				if (r.message){
					r.message.forEach(function(item) {
						frm.add_custom_button(__(item.form_label),
						function() {
							window.open("http://"+ item.form_ip +":"+ item.form_port +"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2F"+ item.form_folder +"&reportUnit=%2FReports%2F"+ item.form_name +"&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
						});
					});
				}
			}
		});
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