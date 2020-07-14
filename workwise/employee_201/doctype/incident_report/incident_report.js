// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

cur_frm.add_fetch('employee', 'department', 'department');
cur_frm.add_fetch('employee', 'full_name', 'employee_name');

frappe.ui.form.on('Incident Report', {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			if (frm.doc.docstatus == 1) {

				frm.add_custom_button(__("Make Notice to Explain"), function() {
					frappe.call({
						method: "make_notice_to_explain",
						doc: frm.doc,
						callback: function(r) {
							frappe.msgprint("Notice to Explain Created: "+r.message);
						}
					});
				}, __("Make"));
				cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
			}
		}
	}, 
	onload_post_render: function() {
	},
});

