// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payroll Register', {

	refresh: function(frm) {
		frappe.call({
    		method: "workwise.payroll.doctype.payroll_register.payroll_register.get_period_status", //dotted path to server method
    		args: {
    		'period':frm.doc.period
    		},
    		callback: function(r) {
    			if(r.message == "2nd"){
    				var host_link = window.location.hostname+":8080";
					frm.add_custom_button(__('COPP_PH'),
					function() {
						window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2Fcopp_ph_&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
					});
					frm.add_custom_button(__('COP_SSS'),
					function() {
						window.open("http://"+host_link+"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2FReports&reportUnit=%2FReports%2Fcopp_sss_&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
					});
    			}
    		}
		})

		frm.disable_save();
	},

});
