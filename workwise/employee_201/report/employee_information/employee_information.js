// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Employee Information"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": "",
			"reqd": 1
		},
		{
			"fieldname":"emp_name",
			"label": __("Employee Name"),
			"fieldtype": "Data",
			"default": ""
		},
		{
			"fieldname":"rate_type",
			"label": __("Rate Type"),
			"fieldtype": "Select",
			"options": ["", "Hourly Rate", "Lead", "Opportunity", "Quotation"],
			"default": ""
		},
	]
}