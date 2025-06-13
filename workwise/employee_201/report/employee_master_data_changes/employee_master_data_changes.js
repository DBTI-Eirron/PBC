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
			options: "\nJob Rotation\nRetirement\nResignation\nRegularization\nRehire\nTransfer\nTermination\nSalary Adjustment\nExtension of Services\nEnd of Contract\nPromotion\nChange of Name\nAdd Bank Details\nChange Bank Details"
		}
	],

	// Use refresh event to apply styling after report loads
	refresh: function(report) {
		// Wait for the report to fully render
		setTimeout(function() {
			// Remove borders from rows containing bold text (headers)
			$('.report-wrapper table tbody tr').each(function() {
				var $row = $(this);
				var firstCell = $row.find('td:first-child');
				
				// Check if first cell contains bold text (header row)
				if (firstCell.find('b').length > 0 || firstCell.html().indexOf('<b>') !== -1) {
					$row.find('td').css({
						'border': 'none',
						'border-top': 'none',
						'border-bottom': 'none',
						'border-left': 'none',
						'border-right': 'none'
					});
				}
				
				// Check if all cells in row are empty (spacer row)
				var isEmpty = true;
				$row.find('td').each(function() {
					if ($(this).text().trim() !== '') {
						isEmpty = false;
						return false;
					}
				});
				
				if (isEmpty) {
					$row.find('td').css({
						'border': 'none',
						'border-top': 'none',
						'border-bottom': 'none',
						'border-left': 'none',
						'border-right': 'none',
						'height': '25px'
					});
				}

				// Style signature-related rows
				var lastThreeCells = $row.find('td').slice(-3); // Get last 3 cells (prepared_by, checked_by, approved_by)
				
				// Check if this is a signature line row (contains underscores)
				if (lastThreeCells.filter(function() { 
					return $(this).text().indexOf('________________________') !== -1; 
				}).length > 0) {
					$row.find('td').css({
						'border': 'none',
						'text-align': 'center',
						'font-weight': 'normal',
						'padding-top': '20px'
					});
				}
				
				// Check if this is a signatory label row (contains "Prepared By", "Checked By", "Approved By")
				if (lastThreeCells.filter(function() { 
					var text = $(this).html();
					return text.indexOf('Prepared By') !== -1 || text.indexOf('Checked By') !== -1 || text.indexOf('Approved By') !== -1;
				}).length > 0) {
					$row.find('td').css({
						'border': 'none',
						'text-align': 'center',
						'font-weight': 'bold',
						'padding-top': '5px'
					});
				}
				

			});
		}, 500); // Wait 500ms for report to render
	}
};