// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Processing', {
	refresh: function(frm){
		frm.disable_save();
		//Button Style
		document.querySelectorAll("[data-fieldname='process_attendance']")[1].style.backgroundColor ="#81da63";
		document.querySelectorAll("[data-fieldname='process_attendance']")[1].style.height ="30px";
		document.querySelectorAll("[data-fieldname='process_attendance']")[1].style.width ="130px";
		document.querySelectorAll("[data-fieldname='process_attendance']")[1].style.color ="white";

		frm.set_query("employee", function() {
			return {
				"filters": {
					"company": frm.doc.company,
					"is_active": 1,
				}
			};
		});

		frm.set_query('period', function(doc) {
			return {
				filters: {
					"time_keeping_status": "Open",
					"company": doc.company
				}
			};
		});

		frm.set_query("location", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});

		frm.set_query("department", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
	},

	setup: function(frm) {
		frm.add_fetch("period", "from_date", "period_from");
		frm.add_fetch("period", "to_date", "period_to");
		frm.add_fetch("period", "schedule", "schedule");
		frm.add_fetch("period", "period_group", "period_group");
	},

	onload: function(frm) {
		
	},
	
	onload_post_render: function() {

	},

	company: function(frm){
		frm.set_value("period", null);
		frm.set_value("period_from", null);
		frm.set_value("period_to", null);
		//frm.set_value("schedule", null);
	}
});

cur_frm.cscript.display_activity_log = function(msg) {
	if(!cur_frm.ss_html)
		cur_frm.ss_html = $a(cur_frm.fields_dict['activity_log'].wrapper,'div');
	if(msg) {
		cur_frm.ss_html.innerHTML =
			'<div class="padding"><h4>'+__("Activity Log:")+'</h4>'+msg+'</div>';
	} else {
		cur_frm.ss_html.innerHTML = "";
	}
}

cur_frm.cscript.process_attendance = function(doc, cdt, cdn) {
	frappe.show_progress("Processing", 87, 100, "Processing Payroll");
	cur_frm.cscript.display_activity_log("");
	var callback = function(r, rt){
		if (r.message)
			frappe.hide_progress();
			cur_frm.cscript.display_activity_log(r.message);
	}
	return $c('runserverobj', args={'method':'process_attendance','docs':doc},callback);
}

