// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Work Suspension', {
	refresh: function(frm) {
		
	},

	add: function(frm) {
		frappe.call({
			method: "get_employees",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

});
cur_frm.fields_dict['apply_to'].grid.get_field('employee').get_query = function(doc, cdt, cdn) {
console.log(doc)
  return{
    filters:{'is_active': "1"}
  }
};

