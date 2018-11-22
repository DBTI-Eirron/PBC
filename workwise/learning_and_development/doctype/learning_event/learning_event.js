// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Learning Event', {
	refresh: function(frm) {
		if (frm.doc.event_status == "Completed"){
			frm.add_custom_button(__('Make Certificates'), function () {
				return frappe.call({
					doc: frm.doc,
					method: 'make_certificates',
					callback: function() {
						frm.refresh();
					}
				});
			});
		}
		
	},

	onload: function(frm){
		frm.set_query("event", function() {
			return {
				"filters": {
					"docstatus": 1,
					"event_status": "Completed",
				}
			};
		});
	},

});
