// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('payroll_period','payroll_date','payroll_date');

frappe.ui.form.on('Bank Remittance Setup', {
	onload: function(frm){
		
	},

	refresh: function(frm) {
		frm.set_query("payroll_period", function() {
			return {
				"filters": {
					"company": frm.doc.company,
					"status": "Closed"
				}
			};
		});
	},

	bank: function(frm) {
		frm.trigger("fill_company");
		frm.trigger("fill_employees");
	},

	company: function(frm) {
		frm.trigger("fill_company");
		frm.trigger("fill_employees");
	},

	payroll_period: function(frm) {
		frm.trigger("fill_employees");
	},

	payroll_schedule: function(frm) {
		frm.trigger("fill_employees");
	},

	payroll_date: function(frm) {
		frm.trigger("fill_employees");
	},
	
	funding_account: function(frm) {
		frm.trigger("fill_employees");
	},

	bank_account_type: function(frm) {
		frm.trigger("fill_employees");
	},

	fill_company: function(frm) {
		if(frm.doc.bank && frm.doc.company) {
			return frappe.call({
				method: "fill_company",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	fill_employees: function(frm) {
		if(frm.doc.bank && frm.doc.company && frm.doc.payroll_period && frm.doc.payroll_date && frm.doc.payroll_schedule && frm.doc.funding_account && frm.doc.bank_account_type) {
			return frappe.call({
				method: "fill_employees",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

});
