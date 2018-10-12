 // Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');

frappe.ui.form.on('DTR Problem Application', {
	onload: function(frm) {

		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today());
		}
		//frm.fields_dict["time_record_request"].grid.set_column_disp('action', false);
		//frm.fields_dict["time_record_request"].grid.toggle_enable("action", false);
		
	},		

	refresh: function(frm) {

	},

});

