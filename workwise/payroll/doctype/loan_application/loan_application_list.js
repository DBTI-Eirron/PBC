// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['Loan Application'] = {
	add_fields: ["unpaid_amount"],
	get_indicator: function(doc) {
		if (flt(doc.unpaid_amount)==0)  {
			return [__("On Hold"), "yellow", "on_hold,=,1"]
		} else if (flt(doc.unpaid_amount)==0) {
			return [__("Paid"), "green", "unpaid_amount,=,0"]
		} else if (flt(doc.unpaid_amount) > 0 ) {
			return [__("Unpaid"), "orange", "unpaid_amount,>,0"]
		} 
	}
};
