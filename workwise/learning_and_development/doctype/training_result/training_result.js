// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Training Result', {
	refresh: function(frm) {

	},

	onload: function(frm) {
		//frm.trigger("training_event");
		frm.get_field('employees').grid.editable_fields = [
			{fieldname: 'hours'}
		];
	},

	training_event: function(frm) {
		frm.trigger("training_event");
	},

	training_event: function(frm) {
		if (frm.doc.training_event && !frm.doc.docstatus && !frm.doc.employees) { 
			frappe.call({
				//method: "workwise.learning_and_development.doctype.training_result.training_result.get_employees",
				//args: {
				//	"training_event": frm.doc.training_event
				//},
				callback: function(r) {
					frm.set_value("employees" ,"");
					if (r.message) {
						$.each(r.message, function(i, d) {
							var row = frappe.model.add_child(cur_frm.doc, "Training Result Employee", "employees");
							row.employee = d.employee;
							row.employee_name = d.employee_name;
						});
					}
					refresh_field("employees");
				}
			});
		}
	}
});
