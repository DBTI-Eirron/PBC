frappe.listview_settings['Loan Application'] = {
	add_fields: ["on_hold", "paid_amount","unpaid_amount"],
	get_indicator: function(doc) {
		if (cint(doc.on_hold) == 1)  {
			return [__("On Hold"), "red"]
		} else if (flt(doc.paid_amount) < 1 && flt(doc.unpaid_amount) > 0 && cint(doc.on_hold) != 1)  {
			return [__("Entered"), "blue"]
		} else if (flt(doc.paid_amount) > 0 && flt(doc.unpaid_amount) > 0 && cint(doc.on_hold != 1) )  {
			return [__("Active"), "orange"]
		} else if (flt(doc.unpaid_amount) == 0 && cint(doc.on_hold != 1) )  {
			return [__("Fully Paid"), "green"]
		} 
	}
};
