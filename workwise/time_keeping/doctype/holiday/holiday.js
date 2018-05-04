// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('payroll_year','from_date','from_date');
cur_frm.add_fetch('payroll_year','to_date','to_date');

frappe.ui.form.on('Holiday', {
	refresh: function(frm) {

	}
});
