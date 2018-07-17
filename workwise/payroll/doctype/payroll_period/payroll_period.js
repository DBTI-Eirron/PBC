// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payroll Period', {
	refresh: function(frm) {
		if(frm.doc.status == 'Closed') {
			frm.add_custom_button(__('Remove Payslips'), function () {
				return frappe.call({
					doc: frm.doc,
					method: 'remove_payslips',
					callback: function() {
						frm.refresh();
					}
				});
			});

			frm.add_custom_button(__('Make Payslips'), function () {
				return frappe.call({
					doc: frm.doc,
					method: 'make_payslips',
					callback: function() {
						frm.refresh();
					}
				});
			});
		}
	},	
});
