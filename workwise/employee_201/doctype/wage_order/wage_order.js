// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt

cur_frm.add_fetch('employee', 'full_name', 'employee_name');
cur_frm.add_fetch('employee', 'rate_type', 'rate_type');
cur_frm.add_fetch('employee', 'rate', 'current_rate');

frappe.ui.form.on('Wage Order', {
	refresh: function(frm) {
		cur_frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});

		cur_frm.set_query("employee", "wage_order", function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return{
				filters: [
					['Employee', 'is_active', '=', 1]
				]
			}
		});
	},

	add_value: function(frm){
		return frappe.call({
			method: "filter_add",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

	reset_employees: function(frm){
		return frappe.call({
			method: "reset_employees",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
});

cur_frm.fields_dict['filter_value'].get_query = function(doc) {
	if(doc.filter_type == "Employee"){
		return {
			filters: {
				"is_active": '1',
				"sensitivity": doc.sensitivity
			}
		}
	}
}