// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Interview and Background', {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			if (frm.doc.docstatus == 1) {
				frm.add_custom_button(__("Make Job Offer"), function() {
					frappe.route_options = {
						"job_applicant": frm.doc.applicant,
						"applicant_name": frm.doc.applicant_name,
					};
					frappe.new_doc("Offer Letter");
				}, __("Make"));
				cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
			}
		}
	},
});
