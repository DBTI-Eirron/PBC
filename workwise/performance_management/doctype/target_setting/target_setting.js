// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('appraisee','company','company');
cur_frm.add_fetch('appraisee','full_name','appraisee_name');
cur_frm.add_fetch('appraisee','position_title','job_title');
cur_frm.add_fetch('appraisee','department','department');
cur_frm.add_fetch('appraisee','date_hired','date_joined');
frappe.ui.form.on('Target Setting', {
	onload: function(frm) {
		if (!frm.doc.planning_date) {
			frm.set_value("planning_date", get_today());
		}
	},
	refresh: function(frm) {

	},
	appraisee: function(frm) {
		frm.trigger("load_appraisee_info");
	},

	load_appraisee_info: function(frm) {
		frm.doc.immediate_supervisor = null;
		frm.doc.immediate_supervisor_name = null;
		frm.doc.supervisor_job_title = null;
		if(frm.doc.appraisee) {
			return frappe.call({
				method: "load_appraisee_info",
				doc: frm.doc,
				callback: function(r) {
					// frm.refresh_field("timelogs_override");
					frm.refresh_fields();

				}
			});
		} 
	},
});
frappe.ui.form.on("Performance Planning KRA", "key_result_area", function(frm, cdt, cdn) {
	return frappe.call({
		method: "change_key_indicator",
		doc: frm.doc,
		callback: function(r) {
			// frm.refresh_field("timelogs_override");
			frappe.meta.get_docfield('Performance Planning KI', 'key_result_area', cur_frm.doc.name).options = r.message;
			cur_frm.refresh_field('key_result_area');
		}
	});
 	//frm.set_df_property('grading_subject', 'options', ['option a', 'option b']);
	// frm.refresh_field('grading_subject');
});
cur_frm.fields_dict['planning_period'].get_query = function(doc) {
	return {
		filters: {
			"status": 'Open'
		}
	}
}
