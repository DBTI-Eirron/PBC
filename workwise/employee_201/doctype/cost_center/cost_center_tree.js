
frappe.treeview_settings['Cost Center'] = {
	ignore_fields:["parent_cost_center"],
	filters: [{
		fieldname: "company",
		fieldtype: "Link",
		options: "Company",
		label: __("Company"),
		reqd: 1,
	}],
	root_label: "Cost Center",
	get_tree_root: false,
}