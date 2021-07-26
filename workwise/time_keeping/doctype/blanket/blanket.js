// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('csa_new_shift','time_in','csa_new_time_in');
cur_frm.add_fetch('csa_new_shift','time_out','csa_new_time_out');

frappe.ui.form.on('Blanket', {
	onload: function(frm){
		frm.set_query('location', function(doc) {
			return {
				filters: {
					"company": doc.company
				}
			};
		});
	},

	refresh: function(frm) {
		cur_frm.set_query("timelogs_application_location", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
		cur_frm.set_query("cost_center", function() {
			return {
				"filters": {
					"timelogs_application_cost_center": frm.doc.company,
				}
			};
		});
	},

	//Filter
	filter_subordinates: function(frm){
		return frappe.call({
			method: "filter_subordinates",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

	filter_company: function(frm){
		return frappe.call({
			method: "filter_company",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

	filter_type: function(frm) {
		frm.set_value("filter_value",null)
	},

	filter_add: function(frm) {
		if(frm.doc.company && frm.doc.filter_value && frm.doc.filter_type) {
			return frappe.call({
				method: "filter_add",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	//Leave Application
	la_leave_type: function(frm) {
		frm.trigger("la_get_dates");
	},

	la_from_date: function(frm) {
		frm.trigger("la_get_dates");
	},

	la_to_date: function(frm) {
		frm.trigger("la_get_dates");
	},

	la_get_dates: function(frm) {
		if(frm.doc.la_leave_type && frm.doc.la_from_date && frm.doc.la_to_date) {
			return frappe.call({
				method: "la_get_dates",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("leave_application_table");
					frm.refresh_fields();
				}
			});
		} 
	},

	//Overtime Application
	ot_from_date: function(frm) {
		frm.trigger("ot_calculate_totals");
	},

	ot_to_date: function(frm) {
		frm.trigger("ot_calculate_totals");
	},

	ot_from_time: function(frm) {
		frm.trigger("ot_calculate_totals");
	},

	ot_to_time: function(frm) {
		frm.trigger("ot_calculate_totals");
	},

	ot_break_hrs: function(frm) {
		frm.trigger("ot_calculate_totals");
	},

	ot_calculate_totals: function(frm) {
		if(frm.doc.ot_from_date && frm.doc.ot_to_date && frm.doc.ot_to_time && frm.doc.ot_from_time) {
			return frappe.call({
				method: "ot_calculate_totals",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	//Official Business Application
	ob_from_date: function(frm) {
		frm.trigger("ob_get_ob_dates");
	},

	ob_to_date: function(frm) {
		frm.trigger("ob_get_ob_dates");
	},
	
	ob_from_time: function(frm) {
		frm.trigger("ob_get_ob_dates");
		frm.trigger("ob_change_time");
	},

	ob_to_time: function(frm) {
		frm.trigger("ob_get_ob_dates");
		frm.trigger("ob_change_time");
	},

	ob_get_ob_dates: function(frm) {
		if(frm.doc.ob_from_date && frm.doc.ob_to_date) {
			return frappe.call({
				method: "ob_get_ob_dates",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("official_business_application_table");
					frm.refresh_fields();
				}
			});
		}
	},

	ob_change_time: function(frm) {
		if(frm.doc.ob_from_time && frm.doc.ob_to_time) {
			return frappe.call({
				method: "ob_change_time",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_field("official_business_application_table");
					frm.refresh_fields();
				}
			});
		}
	},

	//Change Schedule Application
	csa_target_date: function(frm) {
		frm.trigger("csa_get_work_shift");
	},

	csa_get_work_shift: function(frm) {
		if( frm.doc.csa_target_date) {
			return frappe.call({
				method: "csa_get_shift",
				doc: frm.doc,
				callback: function(r) {
					if (!r.exc && r.message) {
						frm.set_value("csa_old_shift", r.message.old_shift);
					}
				}
			});	
		}
	},

	//Excuse Tardiness Application
	eta_date: function(frm) {
		if(frm.doc.eta_date) {
			return frappe.call({
				method: "eta_load_timecard",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	//Compensatory Time Off
	cto_from_time: function(frm) {
		frm.trigger("cto_validate_file_cto");
	},

	cto_to_time: function(frm) {
		frm.trigger("cto_validate_file_cto");
	},

	cto_date: function(frm) {
		frm.trigger("cto_validate_file_cto");
	},

	cto_validate_file_cto: function(frm) {
		if(frm.doc.cto_from_time && frm.doc.cto_to_time && frm.doc.cto_date) {
			return frappe.call({
				method: "cto_validate_file_cto",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	cto_use_fromtime: function(frm) {
		frm.trigger("cto_validate_use_cto");
	},

	cto_use_totime: function(frm) {
		frm.trigger("cto_validate_use_cto");
	},

	cto_use_date: function(frm) {
		frm.trigger("cto_validate_use_cto");
	},

	cto_validate_use_cto: function(frm) {
		if(frm.doc.cto_use_fromtime && frm.doc.cto_use_totime && frm.doc.cto_use_date) {
			return frappe.call({
				method: "cto_validate_date_use_cto",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		} 
	},

	//Timelogs Application
	timelogs_application_location: function(frm) {
		frm.trigger("tla_fill_location_cost_center");
	},

	timelogs_application_cost_center: function(frm) {
		frm.trigger("tla_fill_location_cost_center");
	},

	tla_fill_location_cost_center: function(frm){
		return frappe.call({
			method: "tla_fill_location_cost_center",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("timelogs_application_table");
			}
		});
	},

	tla_fromdate: function(frm) {
		frm.trigger("tla_populate_dates");
	},

	tla_todate: function(frm) {
		frm.trigger("tla_populate_dates");
	},

	tla_populate_dates: function(frm){
		return frappe.call({
			method: "tla_populate_dates",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("timelogs_application_table");
			}
		});
	},

});

frappe.ui.form.on('Blanket Timelogs Application Table', {
	timelogs_application_table_add: function(frm) {
		frappe.call({
			method: "tla_fill_location_cost_center",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("timelogs_application_table");
			}
		});
    },
});
