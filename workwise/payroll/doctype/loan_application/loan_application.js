// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan Application', {
	onload: function(frm){
		
	},

	setup: function(frm) {
		frm.add_fetch("employee", "full_name", "employee_name");
		frm.add_fetch("employee", "company", "company");
		frm.add_fetch("employee", "company", "company");
		frm.add_fetch("loan_type", "title", "loan_name");
	},

	refresh: function(frm) {
		if(frm.doc.docstatus == 1) {
			cur_frm.add_custom_button(__('Make Restructure'), cur_frm.cscript['Make Restructure'], __("Make"));
			cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
		}

		cur_frm.set_query("loan_type", function() {
			return {
				"filters": {
					"entry_type": "Loan",
					"is_active": 1,
				}
			};
		});

		frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});
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

frappe.ui.form.on('Loan Application Payments', {
	before_payments_remove: function (frm, cdt, cdn) {
		if (frm.doc.docstatus == 1){
		let ch = locals[cdt][cdn];
			if(ch.payment_status == "Paid") {
				frappe.throw(__("Cannot delete Paid Row."));
			}	
		}
	}
});

cur_frm.cscript['Make Restructure'] = function() {
	frappe.model.open_mapped_doc({
		method: "workwise.payroll.doctype.loan_application.loan_application.make_restructure",
		frm: cur_frm
	})
}
