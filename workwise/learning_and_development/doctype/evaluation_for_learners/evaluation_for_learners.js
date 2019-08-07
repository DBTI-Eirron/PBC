// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('event', 'learning_program', 'program');

frappe.ui.form.on('Evaluation for Learners', {
	refresh: function(frm) {
		hideTheButtonWrapper = $('*[data-fieldname="evaluation_table"]');
		hideTheButtonWrapper.find('.grid-add-row').hide();
		//hideTheButtonWrapper.find('.grid-remove-row').hide();
		frm.get_field("evaluation_table").grid.only_sortable()
	},

	event: function(frm){
		frappe.call({
			method: "get_evaluation_items",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
});
