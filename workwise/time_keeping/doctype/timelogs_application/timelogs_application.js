// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');

frappe.ui.form.on('Timelogs Application', {
	onload: function(frm) {

	},

	refresh: function(frm) {
		cur_frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});
		cur_frm.set_query("location", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
		cur_frm.set_query("cost_center", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
		cur_frm.fields_dict["timelogs"].grid.get_field("location").get_query = function(doc){
       		return {
           	    filters:{
                    "company": frm.doc.company,
               }
       		}
		}
		cur_frm.fields_dict["timelogs"].grid.get_field("cost_center").get_query = function(doc){
       		return {
           	    filters:{
                    "company": frm.doc.company,
               }
       		}
		}
	},

	location: function(frm) {
		frm.trigger("fill_location_cost_center");
	},

	cost_center: function(frm) {
		frm.trigger("fill_location_cost_center");
	},

	fill_location_cost_center: function(frm){
		if(frm.doc.employee) {
			return frappe.call({
				method: "get_current_timecard",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("timelogs");
				}
			});
		}
	},

	from_date: function(frm) {
		frm.trigger("populate_dates");
	},

	to_date: function(frm) {
		frm.trigger("populate_dates");
	},

	populate_dates: function(frm){
		if(frm.doc.employee) {
			return frappe.call({
				method: "populate_dates",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("timelogs");
				}
			});
		}
	},
});

frappe.ui.form.on("Timelogs Application Table", "target_date", function(frm, cdt, cdn) {
	if(frm.doc.employee) {
		return frappe.call({
			method: "get_current_timecard",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("timelogs");
			}
		});
	}
});

frappe.ui.form.on("Timelogs Application Table", "type", function(frm, cdt, cdn) {
	if(frm.doc.employee) {
		return frappe.call({
			method: "get_current_timecard",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("timelogs");
			}
		});
	}
});