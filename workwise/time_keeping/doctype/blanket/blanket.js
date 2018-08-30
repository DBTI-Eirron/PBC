// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Blanket', {
	onload: function(frm) {
		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today());
		}
	},

	refresh: function(frm) {

	},

	leave_type: function(frm) {
		frm.trigger("get_dates");
	},

	from_date: function(frm) {
		if (frm.doc.application_type=="Leave Application") {
			frm.trigger("get_dates");
		}
		if (frm.doc.application_type=="Official Business Application") {
			frm.trigger("get_ob_dates");
		}
	},

	to_date: function(frm) {
		if (frm.doc.application_type=="Official Business Application") {
			frm.trigger("get_ob_dates");
		}
		if (frm.doc.application_type=="Leave Application") {
			frm.trigger("get_dates");
		}
	},

	company: function(frm) {
		if (frm.doc.application_type=="Official Business Application") {
			frm.trigger("get_ob_dates");
		}
		if (frm.doc.application_type=="Leave Application") {
			frm.trigger("get_dates");
		}
	},

	location: function(frm) {
		if (frm.doc.application_type=="Official Business Application") {
			frm.trigger("get_ob_dates");
		}
		if (frm.doc.application_type=="Leave Application") {
			frm.trigger("get_dates");
		}
	},

	get_dates: function(frm) {
		if(frm.doc.leave_type && frm.doc.from_date && frm.doc.to_date) {
			return frappe.call({
				method: "get_dates",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("leave_application_table");
					frm.refresh_fields();
				}
			});
		} 
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

	csa_dates: function(frm) {
		if( frm.doc.target_date) {
			return frappe.call({
				method: "csa_get_shift",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("csa_table");
					frm.refresh_fields();
				}
			});	
		}
	},

});
