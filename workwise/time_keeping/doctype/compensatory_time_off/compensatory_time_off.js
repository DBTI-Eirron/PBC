// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','full_name','employee_name');
cur_frm.add_fetch('employee','company','company');

frappe.ui.form.on('Compensatory Time Off', {
	onload: function(frm) {
		
	},

	//FILE
	file_from_time: function(frm) {
		frm.trigger("get_target_date");
		//frm.trigger("validate_file_cto");
	},

	file_to_time: function(frm) {
		frm.trigger("get_target_date");
		//frm.trigger("validate_file_cto");
	},

	file_from_date: function(frm) {
		frm.trigger("get_target_date");
		//frm.trigger("validate_file_cto");
	},

	file_to_date: function(frm) {
		frm.trigger("get_target_date");
		//frm.trigger("validate_file_cto");
	},

	validate_file_cto: function(frm) {
		if(frm.doc.file_from_time && frm.doc.file_to_time && frm.doc.file_from_date && frm.doc.file_to_date && frm.doc.file_target_date) {
			return frappe.call({
				method: "file_process_cto",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	use_fromtime: function(frm) {
		frm.trigger("get_target_date");
		frm.trigger("validate_use_cto");
	},

	use_totime: function(frm) {
		frm.trigger("get_target_date");
		frm.trigger("validate_use_cto");
	},

	use_from_date: function(frm) {
		frm.trigger("get_target_date");
		frm.trigger("validate_use_cto");
	},

	use_to_date: function(frm) {
		frm.trigger("get_target_date");
		frm.trigger("validate_use_cto");
	},

	employee: function(frm) {
		frm.trigger("get_target_date");
		frm.trigger("validate_use_cto");
		//frm.trigger("validate_file_cto");
	},

	filed_cto: function(frm) {
		frm.trigger("get_target_date");
		frm.trigger("validate_use_cto");
	},

	validate_use_cto: function(frm) {
		if(frm.doc.use_fromtime && frm.doc.use_totime && frm.doc.use_from_date && frm.doc.use_to_date && frm.doc.use_target_date ) {
			return frappe.call({
				method: "use_process_cto",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	is_previous: function(frm) {
		frm.trigger("get_target_date");
		frm.trigger("validate_use_cto");
	},

	get_target_date: function(frm) {
		if(frm.doc.type) {
			return frappe.call({
				method: "get_target_date",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	refresh: function(frm) {
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
				if (r.message == "forfeit_disabled"){
					cur_frm.toggle_display('filed_cto', false);
				}
				frm.refresh_fields();
			}
		});
	},
	
});
