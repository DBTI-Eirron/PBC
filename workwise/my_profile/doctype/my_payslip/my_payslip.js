// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('My Payslip', {
	onload: function(frm){
		frm.disable_save();
		cur_frm.set_query("payroll_period", function() {
			return {
				"filters": {
					"status": "Closed",
				}
			};
		});
	},

	refresh: function(frm){
		frm.disable_save();
	},

	generate_payslip: function(frm) {
		if(frm.doc.payroll_period) {
			return frappe.call({
				method: "get_payslip",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("payslip_incomes");
					frm.refresh_field("payslip_deductions");
					frm.refresh_fields();
				}
			});
		} 
	},

});
