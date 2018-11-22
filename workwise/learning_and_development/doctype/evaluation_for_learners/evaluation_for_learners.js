// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Evaluation for Learners', {
	refresh: function(frm) {

	},
	onload: function(frm){
		frm.set_query("event", function() {
			return {
				"filters": {
					"docstatus": 1,
					"event_status": "Completed",
				}
			};
		});
	},
});
