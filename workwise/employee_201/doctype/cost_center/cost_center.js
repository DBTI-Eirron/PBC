// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cost Center', {
	refresh: function(frm) {
		frm.trigger("set_root_readonly");
		frm.add_custom_button(__("Cost Center Tree"), function() {
			frappe.set_route("Tree", "Cost Center");
		});

		cur_frm.set_query("parent_cost_center", function() {
		return {
			"filters": [
				['Cost Center', 'name', '!=', 'Cost Center Structure']
				]
			};
		});
	},

	set_root_readonly: function(frm) {
		frm.set_intro("");
		if(frm.doc.is_root) {
			frm.set_read_only();
			frm.set_intro(__("This is a root Cost Center and cannot be edited."), true);
		}
	},
});


