// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Transaction Type', {
	onload: function(frm){
		cur_frm.set_query("loan_against", function() {
			return {
				"filters": {
					"type": "Income",
				}
			};
		});
	},

	refresh: function(frm) {
		cur_frm.set_query("debit_account", "accounts", function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return{
				"filters": {
					"company": d.company,
				}
			}
		});

		cur_frm.set_query("credit_account", "accounts", function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return{
				"filters": {
					"company": d.company,
				}
			}
		});
	},
});
