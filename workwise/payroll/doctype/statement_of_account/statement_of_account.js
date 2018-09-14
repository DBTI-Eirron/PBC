// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Statement of Account', {
	refresh: function(frm) {

	},

	setup: function(frm) {
		frm.add_fetch("period", "from_date", "period_from");
		frm.add_fetch("period", "to_date", "period_to");
	},

});
