// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Batch Approval', {
	onload: function(frm) {
		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today());
		}
		if (!frm.doc.batch_table){
			cur_frm.toggle_display('batch_table',false);
		}
	},
	
	refresh: function(frm) {
		if (!frm.doc.batch_table){
			cur_frm.toggle_display('batch_table',false);
		}
	},

	company: function(frm) {
		frm.trigger("map_applications_on_table");
	},

	from_date: function(frm) {
		frm.trigger("map_applications_on_table");
	},

	to_date: function(frm) {
		frm.trigger("map_applications_on_table");
	},

	application_type: function(frm) {
		frm.trigger("map_applications_on_table");
	},

	employee: function(frm) {
		frm.trigger("map_applications_on_table");
	},

	map_applications_on_table: function(frm) {
		if (frm.doc.company && frm.doc.from_date && frm.doc.to_date && frm.doc.posting_date && frm.doc.application_type) {
			frappe.call({
				method: "map_applications_on_table",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("batch_table");
					if (r){
						cur_frm.toggle_display('batch_table',true);
					}
					frm.refresh_fields();
				}
			});
		}
	},

});
