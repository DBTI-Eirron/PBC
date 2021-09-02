cur_frm.add_fetch('employee','full_name','full_name');
cur_frm.add_fetch('employee','company','company');
cur_frm.add_fetch('employee','department','department');

frappe.ui.form.on('Official Business Application', {
	onload: function(frm) {
		cur_frm.set_query("employee", function() {
			return {
				"filters": {
					"is_active": 1,
				}
			};
		});
	},

	refresh: function(frm) {

	},

	from_date: function(frm) {
		frm.trigger("get_ob_dates");
	},

	to_date: function(frm) {
		frm.trigger("get_ob_dates");
	},
	
	from_time: function(frm) {
		frm.trigger("change_time");
	},

	to_time: function(frm) {
		frm.trigger("change_time");
	},

	get_ob_dates: function(frm) {
		if(frm.doc.from_date && frm.doc.to_date) {
			return frappe.call({
				method: "get_ob_dates",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("official_business_application_table");
					frm.refresh_fields();
				}
			});
		} 
	},
	
	change_time: function(frm) {
		if(frm.doc.from_time || frm.doc.to_time) {
			return frappe.call({
				method: "change_time",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("official_business_application_table");
					frm.refresh_fields();
				}
			});
		} 
	},

});

frappe.ui.form.on("Official Business Application Table", "is_previous", function(frm, cdt, cdn) {
	if(frm.doc.employee) {
		return frappe.call({
			method: "get_target_date",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("official_business_application_table");
				frm.refresh_fields();
			}
		});
	}
});

frappe.ui.form.on("Official Business Application Table", "date", function(frm, cdt, cdn) {
	if(frm.doc.employee) {
		return frappe.call({
			method: "get_target_date",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("official_business_application_table");
				frm.refresh_fields();
			}
		});
	}
});

frappe.ui.form.on("Official Business Application Table", "to_date", function(frm, cdt, cdn) {
	if(frm.doc.employee) {
		return frappe.call({
			method: "get_target_date",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("official_business_application_table");
				frm.refresh_fields();
			}
		});
	}
});