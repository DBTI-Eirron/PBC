// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','full_name');
cur_frm.add_fetch('employee','company','company');

frappe.ui.form.on('Official Business Application', {
	refresh: function(frm) {

	},

	from_date: function(frm) {
		frm.trigger("get_ob_dates");
	},

	to_date: function(frm) {
		frm.trigger("get_ob_dates");
	},

	from_time: function(frm) {
		frm.trigger("set_missing_time");
	},

	to_time: function(frm) {
		frm.trigger("set_missing_time");
	},

	get_ob_dates: function(frm) {
		if(frm.doc.from_date && frm.doc.to_date) {
			return frappe.call({
				method: "get_ob_dates",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("official_business_application_table");
					frm.refresh_fields();
				}
			});
		} 
	},

	set_missing_time: function(frm) {
		if(frm.doc.from_time || frm.doc.to_time) {
			return frappe.call({
				method: "set_missing_time",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("official_business_application_table");
					frm.refresh_fields();
				}
			});
		} 
	},

});
