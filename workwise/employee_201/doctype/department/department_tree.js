
frappe.treeview_settings['Department'] = {
	get_tree_nodes: "workwise.employee_201.doctype.department.department.get_children",
	breadcrumb: "Employee 201",
	title: __("Organization Structure"),
	get_tree_root: true,
	root_label: "Organization Structure",
}