// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('BIR1601 C Form', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1){
			frappe.call({
				method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
				args:{
					doctype_name: "BIR1601 C Form"
				},
				callback: function(r) {
					if (r.message){
						r.message.forEach(function(item) {
							frm.add_custom_button(__(item.form_label),
							function() {
								window.open("http://"+ item.form_ip +":"+ item.form_port +"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2F"+ item.form_folder +"&reportUnit=%2FReports%2F"+ item.form_name +"&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
							});
						});
					}
				}
			});
		}
	},
	company: function(frm) {
		frappe.call({
			method: "compute_value",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	year: function(frm) {
		frappe.call({
			method: "compute_value",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	month: function(frm) {
		frappe.call({
			method: "compute_value",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

	recompute: function(frm) {
		frappe.call({
			method: "recompute_value",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},

	statutory: function(frm) {
		frm.trigger("recompute");
	},
	other_non_taxable_amount: function(frm){
		frm.trigger("recompute");
	},
	total_compensation: function(frm){
		frm.trigger("recompute");
	},
	less_taxable_compensation: function(frm){
		frm.trigger("recompute");
	},
	adjustment_of_taxes: function(frm){
		frm.trigger("recompute");
	},
	total_taxes_withheld: function(frm){
		frm.trigger("recompute");
	},
	less_tax_remitted: function(frm){
		frm.trigger("recompute");
	},
	other_remittance_amount: function(frm){
		frm.trigger("recompute");
	},
	surcharge: function(frm){
		frm.trigger("recompute");
	},
	interest: function(frm){
		frm.trigger("recompute");
	},
	compromise: function(frm){
		frm.trigger("recompute");
	},
});
