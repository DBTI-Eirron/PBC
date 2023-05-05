frappe.listview_settings['Loan Application'] = {
	add_fields: ["status", "on_hold", "paid_amount","unpaid_amount"],
	get_indicator: function (doc) {
		return [__(doc.status), {
			"On Hold": "red",
			"Entered": "blue",
			"Active": "orange",
			"Fully Paid": "green",
		}[doc.status], "status,=," + doc.status];
	}
};