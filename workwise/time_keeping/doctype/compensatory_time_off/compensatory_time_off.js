// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');
cur_frm.add_fetch('employee','department','department');

frappe.ui.form.on('Compensatory Time Off', {
	refresh: function(frm) {
		cur_frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});

		frm.fields_dict['cto_targets'].grid.get_field("filed_cto").get_query = function(doc, cdt, cdn) {
			return {
				filters: [
					['Compensatory Time Off', 'workflow_state', '=', 'Approved'],
					['Compensatory Time Off', 'docstatus', '=', 1],
					['Compensatory Time Off', 'type', '=', 'File'],
					['Compensatory Time Off', 'employee', '=', frm.doc.employee],
					['Compensatory Time Off', 'total_balance', '>', 0],
					['Compensatory Time Off', 'to_date', '<=', frm.doc.to_date],
				]
			}
		},

		frm.fields_dict['cto_targets'].grid.docfields.forEach(function (arrayItem) {
		    var x = arrayItem
	    	if (frm.doc.type=='File'){
	    		if (x['fieldname'] == 'filed_cto'){
	    			x['hidden'] = 1
	    		}
	    		if (x['fieldname'] == 'required_credits'){
	    			x['hidden'] = 1
	    		}
	    		if (x['fieldname'] == 'credits_used'){
	    			x['hidden'] = 0
	    		}
	    		if (x['fieldname'] == 'balance'){
	    			x['hidden'] = 0
	    		}
	    	}else{
	    		if (x['fieldname'] == 'filed_cto'){
	    			frappe.call({
						method: "cto_forfeit_status",
						doc: frm.doc,
						callback: function(r) {
							x['hidden'] = r.message;
							frm.refresh_fields();
						}
					});	
	    		}
	    		if (x['fieldname'] == 'credits_used'){
	    			x['hidden'] = 1
	    		}
	    		if (x['fieldname'] == 'balance'){
	    			x['hidden'] = 1
	    		}
	    		if (x['fieldname'] == 'required_credits'){
	    			x['hidden'] = 0
	    		}
			}
		});
	},

	from_date: function(frm) {
		frm.trigger("js_events");
	},

	to_date: function(frm) {
		frm.trigger("js_events");
	},

	from_time: function(frm) {
		frm.trigger("js_events");
	},

	to_time: function(frm) {
		frm.trigger("js_events");
	},

	type: function(frm) {
		frm.fields_dict['cto_targets'].grid.docfields.forEach(function (arrayItem) {
		    var x = arrayItem
	    	if (frm.doc.type=='File'){
	    		if (x['fieldname'] == 'filed_cto'){
	    			x['hidden'] = 1
	    		}
	    		if (x['fieldname'] == 'required_credits'){
	    			x['hidden'] = 1
	    		}
	    		if (x['fieldname'] == 'credits_used'){
	    			x['hidden'] = 0
	    		}
	    		if (x['fieldname'] == 'balance'){
	    			x['hidden'] = 0
	    		}
	    	}else{
	    		if (x['fieldname'] == 'filed_cto'){
	    			frappe.call({
						method: "cto_forfeit_status",
						doc: frm.doc,
						callback: function(r) {
							x['hidden'] = r.message;
							frm.refresh_fields();
						}
					});	
	    		}
	    		if (x['fieldname'] == 'credits_used'){
	    			x['hidden'] = 1
	    		}
	    		if (x['fieldname'] == 'balance'){
	    			x['hidden'] = 1
	    		}
	    		if (x['fieldname'] == 'required_credits'){
	    			x['hidden'] = 0
	    		}
			}
		});
		frm.trigger("js_events");
	},

	js_events: function(frm) {
		frappe.call({
			method: "js_events",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
});

frappe.ui.form.on("Compensatory Time Off Targets", {
	is_previous: function(frm, cdt, cdn) {
		frappe.call({
			method: "js_table_events",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("cto_targets");
			}
		});
	},

	from_date: function(frm, cdt, cdn) {
		frappe.call({
			method: "js_table_events",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("cto_targets");
			}
		});
	},

	to_date: function(frm, cdt, cdn) {
		frappe.call({
			method: "js_table_events",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("cto_targets");
			}
		});
	},

	from_time: function(frm, cdt, cdn) {
		frappe.call({
			method: "js_table_events",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("cto_targets");
			}
		});
	},

	to_time: function(frm, cdt, cdn) {
		frappe.call({
			method: "js_table_events",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("cto_targets");
			}
		});
	},

	filed_cto: function(frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		frappe.call({
			method: "js_table_events",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("cto_targets");
			}
		});
	},
});