// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Work Shift', {
	refresh: function(frm) {

	},

	calc_work_hours: function(frm) {
		if (!frm.doc.is_flex_shift){
			if( frm.doc.time_in && frm.doc.time_out ) {
				return frappe.call({
					method: "workwise.time_keeping.doctype.work_shift.work_shift.calc_work_hours",
					args: {
						time_in: frm.doc.time_in,
						time_out: frm.doc.time_out,
						break_start: frm.doc.break_start,
						break_end: frm.doc.break_end,
					},
					callback: function(r) {
						if (!r.exc && r.message) {
							frm.set_value("work_hours", r.message.work_hours);
						}
					}
				});	
			}
		}
	},

	calc_break_mins: function(frm) {
		if (!frm.doc.is_flex_shift){
			if( frm.doc.break_start && frm.doc.break_end ) {
				return frappe.call({
					method: "workwise.time_keeping.doctype.work_shift.work_shift.calc_break_mins",
					args: {
						break_start: frm.doc.break_start,
						break_end: frm.doc.break_end,
					},
					callback: function(r) {
						if (!r.exc && r.message) {
							frm.set_value("break_mins", r.message.break_mins);
						}
					}
				});	
			}
		}
	},


});
