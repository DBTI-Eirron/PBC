// Copyright (c) 2019, OSI and contributors
// For license information, please see license.txt

frappe.ui.form.on('BIR2316 Generator', {
	refresh: function(frm) {
		frm.disable_save();
	},
	onload: function(frm) {
		document.querySelectorAll("[data-fieldname='generate_payslip']")[1].style.backgroundColor ="#81da63";
		document.querySelectorAll("[data-fieldname='generate_payslip']")[1].style.height ="30px";
		document.querySelectorAll("[data-fieldname='generate_payslip']")[1].style.width ="130px";
		document.querySelectorAll("[data-fieldname='generate_payslip']")[1].style.color ="white";
	},
	generate_payslip: function(frm){
		frappe.call({
			method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
			args:{
				doctype_name: "BIR2316 Generator"
			},
			callback: function(r) {
				var filter1 = new String("TE.company ='"+frm.doc.company+"'"); 	
				if (frm.doc.employee){
					filter1 += " AND TE.name ='"+frm.doc.employee+"'";
				}
				if (frm.doc.department){
					filter1 += " AND TE.department ='"+frm.doc.department+"'"
				}
				if (frm.doc.location){
					filter1 += " AND TE.location ='"+frm.doc.location+"'";
				}
				if (!frappe.user.has_role("Administrator")){
					filter1 += " AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = '"+frappe.session.user+"')";
				}
				filter1 = filter1.replace('&','xyz123')
				console.log(filter1)
				r.message.forEach(function(item) {
					window.open("http://"+ item.form_ip +":"+ item.form_port +"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2F"+ item.form_folder +"&reportUnit=%2FReports%2F"+ item.form_name +"&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+filter1+"");
				});
			}
		});
	}
});
