// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt
frappe.ui.form.on('Leave Balance', {
	refresh: function(frm) {
		
	},
	onload: function(frm) {
		frm.set_value("cur_balance", Number(parseFloat(frm.doc.credits)).toFixed(2) - Number(parseFloat(frm.doc.used_credits)).toFixed(2));
	},

});
