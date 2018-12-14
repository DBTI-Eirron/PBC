// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Biometrics Device', {
	refresh: function(frm) {

	},

	test_connection: function(frm) {
		//if(frm.doc.company && frm.doc.filter_value && frm.doc.filter_type) {
			return frappe.call({
				method: "test_connection",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		//} 
	},

	force_download: function(frm) {
		//if(frm.doc.company && frm.doc.filter_value && frm.doc.filter_type) {
			return frappe.call({
				method: "force_download",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		//} 
	},
});