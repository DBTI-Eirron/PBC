// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','company','company');
cur_frm.add_fetch('employee','full_name','employee_name');
frappe.ui.form.on('Timelogs Override', {
	
	refresh: function(frm){
		frm.disable_save();
	},

	employee: function(frm) {
		frm.trigger("load_work_schedule");
	},

	load_work_schedule: function(frm) {
		frm.doc.timelogs_override = null;
		frm.refresh_field("timelogs_override");
		if(frm.doc.payroll_period && frm.doc.employee) {
			return frappe.call({
				method: "load_work_schedule",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("timelogs_override");
					frm.refresh_fields();
				}
			});
		} 
	},

	override: function(frm) {
		frappe.call({
			method: "override",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
});

cur_frm.fields_dict['payroll_period'].get_query = function(doc) {
	return {
		filters: {
			"status": 'Open'
		}
	}
}