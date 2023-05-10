// Copyright (c) 2023, OSI and contributors
// For license information, please see license.txt
cur_frm.add_fetch('company','tax_id','tin_number');
cur_frm.add_fetch('company','phone','contact_number');
cur_frm.add_fetch('company','email	','email_address');
cur_frm.add_fetch('company','rdo_code','rdo_code');

frappe.ui.form.on('BIR1601c Form', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1){
			frappe.call({
				method: "hrpx.setup.doctype.jasper_form.jasper_form.get_forms",
				args:{
					doctype_name: "BIR1601c Form"
				},
				callback: function(r) {
					r.message.forEach(function(item) {
						frm.add_custom_button(__(item.form_label),
						function() {
							window.open(item.form_ip +":"+ item.form_port +"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2F"+ item.form_folder +"&reportUnit=%2FReports%2F"+ item.form_name +"&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output="+item.output+"&filter1="+frm.doc.name+"");
						});
					});
				}
			});
		}
	},
	company: function(frm) {
		frappe.call({
			method: "update_data",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
				frappe.call({
					method: "update_totals",
					doc: frm.doc,
					callback: function(r) {
						frm.refresh_fields();
					}
				});
			}
		});
	},
	year: function(frm) {
		frappe.call({
			method: "update_data",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
				frappe.call({
					method: "update_totals",
					doc: frm.doc,
					callback: function(r) {
						frm.refresh_fields();
					}
				});
			}
		});
	},
	month: function(frm) {
		frappe.call({
			method: "update_data",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
				frappe.call({
					method: "update_totals",
					doc: frm.doc,
					callback: function(r) {
						frm.refresh_fields();
					}
				});
			}
		});
	},

	//update Penalties
	surcharge: function(frm) {
		frappe.call({
			method: "update_totals",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	interest: function(frm) {
		frappe.call({
			method: "update_totals",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	compromise: function(frm) {
		frappe.call({
			method: "update_totals",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	less_tax_remitted: function(frm) {
		frappe.call({
			method: "update_totals",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	other_remittance_amount: function(frm) {
		frappe.call({
			method: "update_totals",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	adjustment_of_taxes: function(frm) {
		frappe.call({
			method: "update_totals",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	less_taxable_compensation: function(frm) {
		frappe.call({
			method: "update_totals",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
	other_non_taxable_amount: function(frm) {
		frappe.call({
			method: "update_totals",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_fields();
			}
		});
	},
});
