// Copyright (c) 2020, OSI and contributors
// For license information, please see license.txt

frappe.ui.form.on('Timekeeping Tools', {
	refresh: function(frm) {
		frm.disable_save();
		//Button Style
		document.querySelectorAll("[data-fieldname='force_lb_scheduler']")[1].style.backgroundColor ="#81da63";
		document.querySelectorAll("[data-fieldname='force_lb_scheduler']")[1].style.height ="30px";
		document.querySelectorAll("[data-fieldname='force_lb_scheduler']")[1].style.width ="130px";
		document.querySelectorAll("[data-fieldname='force_lb_scheduler']")[1].style.color ="white";
	},

	force_lb_scheduler: function(frm) {
		frappe.call({
			method: "force_lb_scheduler",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
});