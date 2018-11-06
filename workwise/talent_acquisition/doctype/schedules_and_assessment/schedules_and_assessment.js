// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Schedules and Assessment', {
	refresh: function(frm) {

		if(frm.doc.interview_status == "First") {
			cur_frm.add_custom_button(__('First Interview'), cur_frm.cscript['Make Interview'], __("Make"));
			cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
		} else if (frm.doc.interview_status == "Second"){
			cur_frm.add_custom_button(__('Second Interview'), cur_frm.cscript['Make Interview'], __("Make"));
			cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
		} else if (frm.doc.interview_status == "Third") {
			cur_frm.add_custom_button(__('Third Interview'), cur_frm.cscript['Make Interview'], __("Make"));
			cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
		} else if (frm.doc.interview_status == "Completed") {
			cur_frm.add_custom_button(__('Background Investigation'), cur_frm.cscript['Make Background Investigation'], __("Make"));
			cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
		}


	},

	setup: function(frm) {
		frm.add_fetch("applicant", "applicant_name", "applicant_name");
		frm.add_fetch("initial_interviewer", "full_name", "initial_interviewer_name");
		frm.add_fetch("interviewer", "full_name", "interviewer_name");
		frm.add_fetch("period", "attendance_from", "attendance_from");
		frm.add_fetch("period", "attendance_to", "attendance_to");
		frm.add_fetch("period", "payroll_date", "payroll_date");	
		frm.add_fetch("period", "schedule", "schedule");	
	},
});

cur_frm.cscript['Make Interview'] = function() {
	frappe.model.open_mapped_doc({
		method: "workwise.talent_acquisition.doctype.schedules_and_assessment.schedules_and_assessment.make_interview",
		frm: cur_frm
	})
}

cur_frm.cscript['Make Background Investigation'] = function() {
	frappe.model.open_mapped_doc({
		method: "workwise.talent_acquisition.doctype.schedules_and_assessment.schedules_and_assessment.make_investigation",
		frm: cur_frm
	})
}
