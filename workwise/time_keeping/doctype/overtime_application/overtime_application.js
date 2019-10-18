// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','full_name');
cur_frm.add_fetch('employee','company','company');

frappe.ui.form.on('Overtime Application', {
	onload: function(frm) {
		cur_frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});
	},
	
	refresh: function(frm) {

	},

	from_date: function(frm) {
		frm.trigger("calculate_totals");
		frm.trigger("update_target_date");
	},

	to_date: function(frm) {
		frm.trigger("calculate_totals");
		frm.trigger("update_target_date");
	},

	from_time: function(frm) {
		frm.trigger("calculate_totals");
	},

	to_time: function(frm) {
		frm.trigger("calculate_totals");
	},

	break_hrs: function(frm) {
		frm.trigger("calculate_totals");
	},

	is_previous: function(frm) {
		frm.trigger("update_target_date");
	},

	update_target_date: function(frm) {
		if(frm.doc.employee && frm.doc.from_date && frm.doc.to_date) {
			return frappe.call({
				method: "update_target_date",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		}
	},

	calculate_totals: function(frm) {
		if(frm.doc.employee && frm.doc.from_date && frm.doc.to_date && frm.doc.to_time && frm.doc.from_time) {
			return frappe.call({
				method: "calculate_totals",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

});
