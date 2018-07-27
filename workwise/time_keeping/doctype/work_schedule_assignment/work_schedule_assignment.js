// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Work Schedule Assignment', {
	setup: function(frm){
		frm.add_fetch("employee", "full_name", "employee_name")
	},

	refresh: function(frm){
		frm.disable_save();
	},

	onload_post_render: function() {
		cur_frm.get_field("employees").grid.set_multiple_add("employee");
	},

	filter_subordinates: function(frm){
		return frappe.call({
			method: "filter_subordinates",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

	filter_company: function(frm){
		return frappe.call({
			method: "filter_company",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

	filter_type: function(frm) {
		frm.set_value("filter_value",null)
	},

	filter_add: function(frm) {
		if(frm.doc.company && frm.doc.filter_value && frm.doc.filter_type) {
			return frappe.call({
				method: "filter_add",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},
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

cur_frm.cscript.assign_schedule = function(doc, cdt, cdn) {
	cur_frm.cscript.display_activity_log("");
	var callback = function(r, rt){
		if (r.message)
			cur_frm.cscript.display_activity_log(r.message);
	}
	return $c('runserverobj', args={'method':'assign_schedule','docs':doc},callback);
}

