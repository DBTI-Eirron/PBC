// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan Application', {
	onload: function(frm){
		cur_frm.set_query("loan_type", function() {
			return {
				"filters": {
					"entry_type": "Loan",
					"is_active": 1,
				}
			};
		});
	},

	setup: function(frm) {
		frm.add_fetch("employee", "full_name", "employee_name");
		frm.add_fetch("employee", "company", "company");
		frm.add_fetch("employee", "company", "company");
		frm.add_fetch("loan_type", "title", "loan_name");
	},

	refresh: function(frm) {

	},

	loan_amount: function(frm) {
		frm.trigger("get_total_loan");
	},

	interest: function(frm) {
		frm.trigger("get_total_loan");
	},

	get_total_loan: function(frm) {
		if(frm.doc.loan_amount) {
			return frappe.call({
				method: "get_total_loan",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},
});