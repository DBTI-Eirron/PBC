// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Overtime Rates', {
	onload: function(frm){
		cur_frm.set_query("transaction_type", function() {
			return {
				"filters": {
					"entry_type": "Overtime",
				}
			};
		});
	},

	refresh: function(frm) {

	}
});
