// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Recurring Entry', {
	onload: function(frm){

	},

	setup: function(frm) {
		frm.add_fetch("employee", "full_name", "employee_name");
	},

	refresh: function(frm) {
		cur_frm.set_query("transaction_type", function() {
			return {
				"filters": {
					"is_recurring": 1,
					"is_active": 1,
				}
			};
		});

		//frm.trigger("set_filter_query");
	},


	filter_type: function(frm) {
		frm.set_value("filter_value",null)
		if(frm.doc.filter_type == "Employee") {
			cur_frm.set_query("filter_value", function() {
				return {
					"filters": {
						"is_active": 1,
					}
				};
			});
		} else {
			cur_frm.set_query("filter_value", function() {
				return {};
			});			
		}
	},

	filter_add: function(frm) {
		if(frm.doc.filter_value && frm.doc.filter_type) {
			return frappe.call({
				method: "filter_add",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		}
	},

	filter_add_company: function(frm) {
		if(frm.doc.company) {
			return frappe.call({
				method: "filter_add_company",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		}
	},

	filter_reset: function(frm) {	
		return frappe.call({
			method: "filter_reset",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});	
	},
});
