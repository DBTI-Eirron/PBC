cur_frm.add_fetch('employee','full_name','full_name');
cur_frm.add_fetch('employee','company','company');

frappe.ui.form.on('Official Business Application', {
	onload: function(frm) {
		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today());
		}
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
