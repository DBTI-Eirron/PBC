// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Background Investigation', {
	refresh: function(frm) {
		if (!frm.doc.__islocal) {
			if (frm.doc.docstatus == 1 && frm.doc.investigation_status == "Passed") {
				cur_frm.add_custom_button(__('Job Offer'), cur_frm.cscript['Make Job Offer'], __("Make"));
				cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
			}
		}
	},


});

cur_frm.cscript['Make Job Offer'] = function() {
	frappe.model.open_mapped_doc({
		method: "workwise.talent_acquisition.doctype.background_investigation.background_investigation.make_offer",
		frm: cur_frm
	})
}