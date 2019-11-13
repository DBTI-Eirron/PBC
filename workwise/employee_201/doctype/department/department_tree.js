
frappe.treeview_settings['Department'] = {
	ignore_fields:["parent_department"],
	filters: [{
		fieldname: "company",
		fieldtype: "Link",
		options: "Company",
		label: __("Company"),
		reqd: 1,
	}],
	root_label: "Departments",
	get_tree_root: false,
}