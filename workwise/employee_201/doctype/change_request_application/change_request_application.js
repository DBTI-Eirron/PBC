// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','full_name');
cur_frm.add_fetch('employee','company','company');
cur_frm.add_fetch('employee','department','department');

frappe.ui.form.on('Change Request Application', {
	refresh: function(frm) {
		cur_frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});

		frm.trigger("filter_employee_address");
		frm.trigger("display_tables");
	},

	//Filter employee address
	filter_employee_address: function(frm) {
		var address_list = [];
		frappe.call({
			method: "get_employee_address",
			doc: frm.doc,
			async: false,
			callback: function(r) {
				address_list = r.message;
			}
		});
		frm.fields_dict['change_request_address'].grid.get_field("address").get_query = function(doc, cdt, cdn) {
			return {
				filters: [
					['Address', 'name', 'in', address_list]
				]
			}
		}
		frm.refresh_field("change_request_address");
	},

	//Filter employee contact
	filter_employee_contact: function(frm) {
		var address_list = [];
		frappe.call({
			method: "get_employee_contact",
			doc: frm.doc,
			async: false,
			callback: function(r) {
				address_list = r.message;
			}
		});
		frm.fields_dict['change_request_contact'].grid.get_field("contact").get_query = function(doc, cdt, cdn) {
			return {
				filters: [
					['Contact', 'name', 'in', address_list]
				]
			}
		}
		frm.refresh_field("change_request_contact");
	},

	employee: function(frm) {
		frm.trigger("filter_employee_address");
		frm.trigger("filter_employee_contact");
		frm.trigger("clear_tables");
	},

	item_category: function(frm) {
		frm.trigger("filter_employee_address");
		frm.trigger("filter_employee_contact");
		frm.trigger("display_tables");
		frm.trigger("clear_tables");
	},

	clear_tables: function(frm) {
		cur_frm.clear_table("change_request");
		cur_frm.clear_table("change_request_address");
		cur_frm.clear_table("change_request_contact");
		cur_frm.refresh_fields();
	},

	display_tables: function(frm) {
		cur_frm.toggle_display('requested_item',false);
		cur_frm.toggle_display('address_item_request',false);
		cur_frm.toggle_display('contact_item_request',false);
		if (frm.doc.item_category == "Address"){
			cur_frm.toggle_display('requested_item',false);
			cur_frm.toggle_display('address_item_request',true);
			cur_frm.toggle_display('contact_item_request',false);
		}else if(frm.doc.item_category == "Contact"){
			cur_frm.toggle_display('requested_item',false);
			cur_frm.toggle_display('address_item_request',false);
			cur_frm.toggle_display('contact_item_request',true);
		}else{
			cur_frm.toggle_display('requested_item',true);
			cur_frm.toggle_display('address_item_request',false);
			cur_frm.toggle_display('contact_item_request',false);
		}
	},
});

frappe.ui.form.on("Change Request Application Table", "item", function(frm, cdt, cdn) {
	var d = locals[cdt][cdn];
	return frappe.call({
		method: "get_request",
		doc: frm.doc,
		callback: function(r) {
			frm.refresh_fields();
		}
	});
});

frappe.ui.form.on("Change Request Address Table", "item", function(frm, cdt, cdn) {
	var d = locals[cdt][cdn];
	return frappe.call({
		method: "get_request_address",
		doc: frm.doc,
		callback: function(r) {
			frm.refresh_fields();
		}
	});
});

frappe.ui.form.on("Change Request Contact Table", "item", function(frm, cdt, cdn) {
	var d = locals[cdt][cdn];
	return frappe.call({
		method: "get_request_contact",
		doc: frm.doc,
		callback: function(r) {
			frm.refresh_fields();
		}
	});
});