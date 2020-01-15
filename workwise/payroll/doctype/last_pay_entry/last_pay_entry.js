// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Last Pay Entry', {
	refresh: function(frm) {

	},

	setup: function(frm) {
		frm.add_fetch("employee", "full_name", "employee_name");
		frm.add_fetch("employee", "company", "company");
		frm.add_fetch("payroll_year", "from_date", "from_year");
		frm.add_fetch("payroll_year", "to_date", "to_year");
	},
	
	get_last_pay: function(frm) {
		if(frm.doc.employee && frm.doc.payroll_year && frm.doc.from_year){
			return frappe.call({
				method: "get_register",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	employee: function(frm) {
		frm.trigger("validate_dates");
	},

	payroll_year: function(frm) {
		frm.trigger("validate_dates");
	},

	validate_dates: function(frm) {
		if(frm.doc.employee && frm.doc.payroll_year){
			return frappe.call({
				method: "validate_dates",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},
});
