// Copyright (c) 2018, HDI Systech and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee','date_hired','from_date');
cur_frm.add_fetch('employee','date_resigned','to_date');

frappe.ui.form.on('BIR2316', {
	onload: function(frm) {
		
	},

	refresh: function(frm) {
		var host_link = window.location.hostname+":8080";
		if(frm.doc.docstatus == 1){
			frm.add_custom_button(__('Print BIR2316'),
			function() {
				window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2FBIR2316&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
			});
		}
	},

	document_type: function(frm){
		if(frm.doc.document_type == "Previous"){
			frm.set_df_property("employer_section", "read_only", 0);
			frm.refresh_fields();
		}
	},

	setup: function(frm) {
		frm.add_fetch("employee", "full_name", "employee_name");
	},
});
