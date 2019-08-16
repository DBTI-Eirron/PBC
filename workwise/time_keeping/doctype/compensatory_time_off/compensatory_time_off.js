// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');

frappe.ui.form.on('Compensatory Time Off', {
	onload: function(frm) {
		cur_frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});

		frm.set_query('filed_cto', function(doc) {
			if(frm.doc.employee && frm.doc.type == "Use"){
				return {
					filters: {
						"workflow_state": 'Approved',
						"docstatus": 1,
						"type": "File",
						"employee": doc.employee,
						"balance": ['>',0]
					}
				};
			}else{
				return {
					filters: {
						"type": "",
					}
				};
			}
		});
			
		frappe.call({
			method: "get_timekeeping_settings_for_cto_use_type",
			doc: frm.doc,
			callback: function(r) {
				if (r.message == "hour"){
					cur_frm.toggle_display('filed_cto', false);
				}
				frm.refresh_fields();
			}
		});	
		
	},

	from_time: function(frm) {
		frm.trigger("validate_file_cto");
	},

	to_time: function(frm) {
		frm.trigger("validate_file_cto");
	},

	date: function(frm) {
		frm.trigger("validate_file_cto");
	},

	validate_file_cto: function(frm) {
		if(frm.doc.from_time && frm.doc.to_time && frm.doc.date) {
			return frappe.call({
				method: "validate_file_cto",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	use_fromtime: function(frm) {
		frm.trigger("validate_use_cto");
	},

	use_totime: function(frm) {
		frm.trigger("validate_use_cto");
	},

	use_date: function(frm) {
		frm.trigger("validate_use_cto");
	},

	employee: function(frm) {
		frm.trigger("validate_use_cto");
	},

	filed_cto: function(frm) {
		frm.trigger("validate_use_cto");
	},

	validate_use_cto: function(frm) {
		if(frm.doc.use_fromtime && frm.doc.use_totime && frm.doc.use_date ) {
			return frappe.call({
				method: "validate_use_cto",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	refresh: function(frm) {

	},
	
});
