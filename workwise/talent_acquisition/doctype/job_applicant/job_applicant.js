// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Job Applicant', {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			if (frm.doc.docstatus == 1) {
				frm.add_custom_button(__("Make Schedules and Assessment"), function() {
					frappe.route_options = {
						"applicant": frm.doc.name,
						"applicant_name": frm.doc.applicant_name,
						"apply_for": frm.doc.apply_for,
					};
					frappe.new_doc("Schedules and Assessment");
				}, __("Make"));
				cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
			}
		}
	},
});
