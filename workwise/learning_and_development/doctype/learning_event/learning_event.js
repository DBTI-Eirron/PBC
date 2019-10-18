// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Learning Event', {
	refresh: function(frm) {
		if (frm.doc.event_status == "Completed"){
			frm.add_custom_button(__('Make Certificates'), function () {
				return frappe.call({
					doc: frm.doc,
					method: 'make_certificates',
					callback: function() {
						frm.refresh();
					}
				});
			});
		}

		if(frm.doc.docstatus == 1) {
			cur_frm.add_custom_button(__('Update Status'), cur_frm.cscript['Update Status'], __("Update"));
			cur_frm.page.set_inner_btn_group_as_primary(__("Update"));
		}
		
	},

	onload: function(frm){
		frm.set_query("event", function() {
			return {
				"filters": {
					"docstatus": 1,
					"event_status": "Completed",
				}
			};
		});
	},

	learning_program: function(frm){
		frappe.call({
			method: "get_learning_program",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

});

cur_frm.cscript['Update Status'] = function() {
	frappe.model.open_mapped_doc({
		method: "workwise.learning_and_development.doctype.learning_event.learning_event.update_status",
		frm: cur_frm
	})
}

//frappe.ui.form.on("Learning Participants", "program", function(frm, cdt, cdn) {
//	if(frm.doc.learning_program) {
//		return frappe.call({
//			method: "select_program_session",
//			doc: frm.doc,
//			callback: function(r) {
//				frappe.meta.get_docfield('Learning Participants', 'program', cur_frm.doc.name).options = ['', 'Option 1', 'Option 2', 'Option 3'];
//				cur_frm.refresh_field('participants');
//			}
//		});
//	}
//});