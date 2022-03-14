// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Talent Acquisition Planning', {
	refresh: function(frm) {
	},

	setup: function(frm) {
		frm.set_query("department", function() {
			return {
				filters: [
					["Department","company", "=", frm.doc.company]
				]
			}
		});
		frappe.ui.form.on('Talent Acquisition Planning Position', {
			rate: function(frm, cdt, cdn) {
				var row = frappe.get_doc(cdt, cdn);
				if(row.rate && row.qty){
					var amount = flt(row.rate * row.qty);
					frappe.model.set_value(cdt, cdn, 'amount', amount);
					frm.trigger('calculate_net_total');					
				} else {
					frappe.model.set_value(cdt, cdn, 'amount', 0);
					frm.trigger('calculate_net_total');
				}
			},

			qty: function(frm, cdt, cdn) {
				var row = frappe.get_doc(cdt, cdn);
				if(row.rate && row.qty){
					var amount = flt(row.rate * row.qty);
					frappe.model.set_value(cdt, cdn, 'amount', amount);
					frm.trigger('calculate_net_total');					
				} else {
					frappe.model.set_value(cdt, cdn, 'amount', 0);
					frm.trigger('calculate_net_total');
				}
			},			
		});


	},

	calculate_net_total: function(frm) {
		var positions = frm.doc.positions;
		var budget_amount = 0.0;

		positions.forEach(function(item) {
			budget_amount += item.amount;
		});

		frm.set_value('budget_amount', budget_amount);
	},


});
