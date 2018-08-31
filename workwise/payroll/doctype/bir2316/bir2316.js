// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('BIR2316', {
	refresh: function(frm) {

	},

	setup: function(frm) {
		frm.add_fetch("employee", "full_name", "employee_name");
	},

	get_info: function(frm) {
		if(frm.doc.employee && frm.doc.from_date && frm.doc.to_date){
			return frappe.call({
				method: "get_info",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},
});
