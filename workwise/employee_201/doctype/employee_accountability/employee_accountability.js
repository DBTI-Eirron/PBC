// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt

cur_frm.add_fetch('employee_id', 'department', 'department');
cur_frm.add_fetch('employee_id', 'company', 'company');
cur_frm.add_fetch('employee_id', 'full_name', 'employee_name');

frappe.ui.form.on('Employee Accountability', {
	refresh: function(frm) {
		if (frm.doc.__islocal){
			frappe.call({
				method: "validate_fields",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("employee_id");
					frm.refresh_field("employee_name");
				}
			});
		}

		if (frm.doc.type == 'Return'){
			cur_frm.toggle_display('return_section',true);
			cur_frm.toggle_display('issuance_section',false);
		}

		if (frm.doc.type == 'Issuance'){
			cur_frm.toggle_display('issuance_section',true);
			cur_frm.toggle_display('return_section',false);
		}
	},

	employee_id: function(frm) {
		frm.trigger("get_issuance");
	},

	type: function(frm) {
		if (frm.doc.type == 'Return'){
			cur_frm.toggle_display('return_section',true);
			cur_frm.toggle_display('issuance_section',false);
			frm.trigger("get_issuance");
		}

		if (frm.doc.type == 'Issuance'){
			cur_frm.toggle_display('issuance_section',true);
			cur_frm.toggle_display('return_section',false);
		}
	},

	get_issuance: function(frm){
		if (frm.doc.company && frm.doc.employee_id && frm.doc.type == 'Return' && frm.doc.docstatus == 0){
			return frappe.call({
				method: "get_issuance",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("return_table");
				}
			});
		}
	},
});

//frappe.ui.form.on("Accountability Issuance Table", "item_name", function(frm, cdt, cdn) {
//	return frappe.call({
//		method: "set_issued_by",
//		doc: frm.doc,
//		callback: function(r) {
//			frm.refresh_field("issuance_table");
//		}
//	});
//});