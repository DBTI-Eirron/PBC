// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payroll Processing', {
	onload: function(frm){
		frm.set_query('period', function(doc) {
			return {
				filters: {
					"status": "Open",
					"company": doc.company
				}
			};
		});
	},

	setup: function(frm) {
		frm.add_fetch("period", "frequency", "frequency");
		frm.add_fetch("period", "from_date", "period_from");
		frm.add_fetch("period", "to_date", "period_to");
		frm.add_fetch("period", "attendance_from", "attendance_from");
		frm.add_fetch("period", "attendance_to", "attendance_to");
		frm.add_fetch("period", "payroll_date", "payroll_date");	
		frm.add_fetch("period", "schedule", "schedule");	
	},

	refresh: function(frm) {
		frm.disable_save();
	},
	
	onload_post_render: function() {

	},

	company: function(frm){
		frm.set_value("period", null);
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

cur_frm.cscript.process_payroll = function(doc, cdt, cdn) {
	frappe.show_progress("Processing", 87, 100, "Processing Payroll");
	cur_frm.cscript.display_activity_log("");
	var callback = function(r, rt){
		if (r.message)
			frappe.hide_progress();
			cur_frm.cscript.display_activity_log(r.message);
	}
	return $c('runserverobj', args={'method':'process_payroll','docs':doc},callback);
}
