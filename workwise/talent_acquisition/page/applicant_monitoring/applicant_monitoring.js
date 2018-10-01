frappe.pages['applicant_monitoring'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Applicant Monitoring',
		single_column: true
	});

	frappe.modules_page = page;

	frappe.call({
		method: "workwise.talent_acquisition.page.applicant_monitoring.applicant_monitoring.get_candidates",
		callback: function(r) {
			if (!r.exc && r.message) {
				var candidates = r.message.candidates;
				var for_assessment = r.message.for_assessment;
				var for_interview = r.message.for_interview;
				var job_offer = r.message.job_offer;
				page.main.html(frappe.render_template('monitor_section', {candidates:candidates, for_assessment:for_assessment, for_interview:for_interview, job_offer: job_offer} ));
			}
		}
	});

}