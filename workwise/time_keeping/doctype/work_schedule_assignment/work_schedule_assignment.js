// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Work Schedule Assignment', {
	refresh: function(frm){
		frm.disable_save();
		frm.add_fetch("employee", "full_name", "employee_name")
	},

	onload_post_render: function() {
		cur_frm.get_field("employees").grid.set_multiple_add("employee");
	},

	filter_subordinates: function(frm){
		return frappe.call({
			method: "filter_add",
			doc: frm.doc,
			args: {
				entry: 'Subordinates'
			},
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

	filter_company: function(frm){
		return frappe.call({
			method: "filter_add",
			doc: frm.doc,
			args: {
				entry: 'Company'
			},
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

	filter_type: function(frm) {
		frm.set_value("filter_value",null);
	},

	filter_add: function(frm) {
		if(frm.doc.company) {
			return frappe.call({
				method: "filter_add",
				doc: frm.doc,
				args: {
					entry: 'Employee'
				},
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	assignment: function(frm) {
		frm.trigger("clear_tables");
		frm.set_value("filter_type", "Employee");
	},

	from_date: function(frm) {
		frm.trigger("validate_employees");
	},

	to_date: function(frm) {
		frm.trigger("validate_employees");
	},

	validate_employees: function(frm) {
		if(frm.doc.company && frm.doc.from_date && frm.doc.to_date) {
			return frappe.call({
				method: "validate_employees",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	clear_tables: function(frm) {
		return frappe.call({
			method: "clear_tables",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});	
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

cur_frm.fields_dict['filter_value'].get_query = function(doc) {
	if(doc.filter_type == "Employee"){
		return {
			filters: {
				"company": cur_frm.doc.company,
				"is_active": '1'
			}
		}
	}
}