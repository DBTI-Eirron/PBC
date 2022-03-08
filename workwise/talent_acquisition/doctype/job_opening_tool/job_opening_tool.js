// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Job Opening Tool', {
	refresh: function(frm) {

	},
	setup: function(frm) {
		frm.set_query("job_opening", function() {
			return {
				filters: [
					["Job Opening","position_title", "=", frm.doc.name],
					["Job Opening","status", "=", "Open"]
				]
			}
		});
	},
});
