 // Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');

frappe.ui.form.on('DTR Problem Application', {
	onload: function(frm) {
		if (!frm.doc.date_submitted) {
			frm.set_value("date_submitted", get_today());
		}
	},

	refresh: function(frm) {

	},

});
