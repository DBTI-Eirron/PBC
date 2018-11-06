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
				var schedule_assessment = r.message.schedule_assessment;
				var interview = r.message.interview;
				var background_investigation = r.message.background_investigation;
				var job_offer = r.message.job_offer;
				var contract_signing = r.message.contract_signing;
				var for_employee = r.message.for_employee;
				var ar = r.message.ar;
				
				page.main.html(frappe.render_template('monitor_section', {
					candidates: candidates, 
					schedule_assessment: schedule_assessment, 
					interview: interview, 
					background_investigation: background_investigation,
					
					job_offer: job_offer,
					contract_signing: contract_signing,
					for_employee: for_employee, 
					//onboarding: onboarding, 
					ar: ar } 
				));

				var post_btn = page.wrapper.find(".btn-post").on("click", function() {
					frappe.new_doc('Job Applicant');
				});
			}
		}
	});

}