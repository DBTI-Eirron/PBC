// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Work Suspension', {
	refresh: function(frm) {
		
	},

	from_date: function(frm) {
		frm.trigger("get_dates");	},

	to_date: function(frm) {
		frm.trigger("get_dates");
	},

	get_dates: function(frm) {
		if(frm.doc.from_date && frm.doc.to_date) {
			return frappe.call({
				method: "get_dates",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("dates");
					frm.refresh_fields();
				}
			});
		} 
	},

	company: function(frm) {
		frm.doc.apply_to = null
		frappe.call({
			method: "add",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	location: function(frm) {
		frm.doc.apply_to = null
		frappe.call({
			method: "add",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	department: function(frm) {
		frm.doc.apply_to = null
		frappe.call({
			method: "add",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

	// add: function(frm) {
	// 	frm.doc.apply_to = null
	// 	frappe.call({
	// 		method: "add",
	// 		doc: frm.doc,
	// 		callback: function(r) {
	// 			frm.refresh_fields();
	// 		}
	// 	});
	// },

});
