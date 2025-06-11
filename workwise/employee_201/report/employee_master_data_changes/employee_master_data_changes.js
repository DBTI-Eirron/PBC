// Copyright (c) 2016, OSI and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Master Data Changes"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1
		},
		{
			fieldname: "payroll_period",
			label: __("Payroll Period"),
			fieldtype: "Link",
			options: "Payroll Period",
			reqd: 1
		},
		{
			fieldname: "period_group",
			label: __("Period Group"),
			fieldtype: "Link",
			options: "Period Group",
			// reqd: 1
		},
		{
			fieldname: "movement_type",
			label: __("Movement Type"),
			fieldtype: "Select",
			options: `
					Job Rotation
					Retirement
					Resignation
					Regularization
					Rehire
					Transfer
					Termination
					Salary Adjustment
					Extension of Services
					End of Contract
					Promotion
					Change of Name
					Add Bank Details
					Change Bank Details`,
		}

		// {
		// 	fieldname: "from_date",
		// 	label: __("From Date"),
		// 	fieldtype: "Date",
		// 	"reqd": 1
		// },
		// {
		// 	fieldname: "to_date",
		// 	label: __("To Date"),
		// 	fieldtype: "Date",
		// 	"reqd": 1
		// }
	]
}
