// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Training Needs Analysis', {
	refresh: function(frm) {

	},

	training_name: function(frm) {
		frm.trigger("get_sessions");
	},

	get_sessions: function(frm) {
		if(frm.doc.training_name) {
			return frappe.call({
				method: "get_sessions",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	department: function(frm) {
		frm.trigger("get_employees");
	},

	get_employees: function(frm) {
		if(frm.doc.type == "Department" && frm.doc.department) {
			return frappe.call({
				method: "get_employees",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

});
