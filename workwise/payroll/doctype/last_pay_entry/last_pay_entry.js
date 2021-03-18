// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt


frappe.ui.form.on('Last Pay Entry', {
	onload: function(frm){
		//Button Style
		document.querySelectorAll("[data-fieldname='auto_entries']")[1].style.backgroundColor ="#81da63";
		document.querySelectorAll("[data-fieldname='auto_entries']")[1].style.height ="30px";
		document.querySelectorAll("[data-fieldname='auto_entries']")[1].style.width ="120px";
		document.querySelectorAll("[data-fieldname='auto_entries']")[1].style.color ="white";
	},

	refresh: function(frm) {

	},

	setup: function(frm) {
		frm.add_fetch("employee", "full_name", "employee_name");
		frm.add_fetch("employee", "company", "company");
		frm.add_fetch("employee", "department", "department");
		frm.add_fetch("employee", "position_title", "position_title");
		frm.add_fetch("employee", "sensitivity", "sensitivity_level");
		frm.add_fetch("payroll_year", "from_date", "from_year");
		frm.add_fetch("payroll_year", "to_date", "to_year");
		frm.add_fetch("transaction_type", "type", "type");
	},
	
	auto_entries: function(frm) {
		if(frm.doc.employee && frm.doc.payroll_year && frm.doc.from_year){
			return frappe.call({
				method: "get_auto_entries",
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
