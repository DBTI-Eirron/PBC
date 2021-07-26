// Copyright (c) 2019, HDI Systech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payslip Generator', {
	refresh: function(frm) {
		frm.disable_save();
	},
	onload: function(frm) {
		document.querySelectorAll("[data-fieldname='generate_payslip']")[1].style.backgroundColor ="#81da63";
		document.querySelectorAll("[data-fieldname='generate_payslip']")[1].style.height ="30px";
		document.querySelectorAll("[data-fieldname='generate_payslip']")[1].style.width ="100px";
		document.querySelectorAll("[data-fieldname='generate_payslip']")[1].style.color ="white";

		frm.set_query('payroll_period', function(doc) {
			return {
				filters: {
					"status": "Open",
					"company": doc.company
				}
			};
		});
	},

	generate_payslip: function(frm){
		frappe.call({
			method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
			args:{
				doctype_name: "My Payslip"
			},
			callback: function(r) {
				var filter1 = new String("PR.company = '"+frm.doc.company+"' AND PR.period = '"+frm.doc.payroll_period+"'");
				if (!frappe.user.has_role("Administrator")){
					filter1 += " AND E.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = '"+frappe.session.user+"')";
				}
				if (r.message){
					r.message.forEach(function(item) {
						window.open("http://"+ item.form_ip +":"+ item.form_port +"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2F"+ item.form_folder +"&reportUnit=%2FReports%2F"+ item.form_name +"&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+filter1+"");
					});
				}
			}
		});
	}
});
