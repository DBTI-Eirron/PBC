// Copyright (c) 2017, HDI Systech and contributors
// For license information, please see license.txt

cur_frm.add_fetch('employee', 'full_name', 'employee_name');
cur_frm.add_fetch('employee', 'sensitivity', 'sensitivity_level');
cur_frm.add_fetch('employee', 'company', 'company');
cur_frm.add_fetch('employee', 'position_title', 'current_position');
cur_frm.add_fetch('employee', 'job_level', 'current_job_level');
cur_frm.add_fetch('employee', 'employment_status', 'current_employment_status');
cur_frm.add_fetch('employee', 'employment_status', 'employment_status');
cur_frm.add_fetch('employee', 'company', 'current_company');
cur_frm.add_fetch('employee', 'department', 'current_department');
cur_frm.add_fetch('employee', 'location', 'current_location');
cur_frm.add_fetch('employee', 'end_of_contract', 'current_end_of_contract');
cur_frm.add_fetch('employee', 'date_hired', 'current_date_hired');
cur_frm.add_fetch('employee', 'rate_type', 'current_rate_type');
cur_frm.add_fetch('employee', 'cost_center', 'current_cost_center');
//cur_frm.add_fetch('employee', 'rate', 'current_rate');
//cur_frm.add_fetch('employee', 'min_take_home', 'current_minimum_take_home');
cur_frm.add_fetch('employee', 'is_attendance_base', 'current_attendance_base');

cur_frm.add_fetch('employee', 'position_title', 'new_position');
cur_frm.add_fetch('employee', 'job_level', 'new_job_level');
cur_frm.add_fetch('employee', 'employment_status', 'change_employment_status');
cur_frm.add_fetch('employee', 'position_title', 'current_position_title');
cur_frm.add_fetch('employee', 'department', 'new_department');
cur_frm.add_fetch('employee', 'location', 'new_location');
cur_frm.add_fetch('employee', 'end_of_contract', 'new_end_of_contract');
cur_frm.add_fetch('employee', 'date_hired', 'new_date_hired');
cur_frm.add_fetch('employee', 'rate_type', 'new_rate_type');
//cur_frm.add_fetch('employee', 'rate', 'new_rate');
//cur_frm.add_fetch('employee', 'min_take_home', 'new_minimum_take_home');
cur_frm.add_fetch('employee', 'is_attendance_base', 'new_attendance_base');

frappe.ui.form.on('Employee Movement', {
	onload: function(frm) {
		if (frm.doc.__islocal){
			frm.set_value("employee", "");
		}
	},
	
	on_submit: function(frm) {
		if (frm.doc.movement_type == 'Rehire'){
			frappe.set_route('Form', 'Employee', frm.doc.created_employee);
		}
	},

	refresh: function(frm) {
		frm.trigger("filter_employees");
		if(frm.doc.docstatus == 1){
			frappe.call({
				method: "workwise.setup.doctype.jasper_form.jasper_form.get_forms",
				args:{
					doctype_name: "Employee Movement"
				},
				callback: function(r) {
					r.message.forEach(function(item) {
						frm.add_custom_button(__(item.form_label),
						function() {
							window.open("http://"+ item.form_ip +":"+ item.form_port +"/jasperserver/flow.html?_flowId=viewReportFlow&_flowId=viewReportFlow&ParentFolderUri=%2F"+ item.form_folder +"&reportUnit=%2FReports%2F"+ item.form_name +"&standAlone=true&j_username=jasperadmin&j_password=jasperadmin&output=pdf&filter1="+frm.doc.name+"");
						});
					});
				}
			});
		}
	},

	employee: function(frm) {
		frm.trigger("filter_employees");
		if (frm.doc.employee){
			frappe.call({
				method: "get_employee_details",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		}
	},

	movement_type: function(frm) {
		frm.trigger("get_clear_types");
		if (frm.doc.movement_type == "Regularization"){
			frm.trigger("get_regularization");
		}
		if (frm.doc.movement_type == "Retirement"){
			frm.trigger("get_retirement");
		}
		if (frm.doc.movement_type == "Resignation"){
			frm.trigger("get_resignation");
		}
		frm.trigger("filter_employees");
	},

	get_resignation: function(frm) {
		frm.set_value("change_employment_status", "Resigned");
	},

	get_retirement: function(frm) {
		frm.set_value("change_employment_status", "Retired");
	},

	get_clear_types: function(frm) {
		frm.set_value("termination_due_to", "");
		frm.set_value("change_employment_status", "");
	},

	get_regularization: function(frm) {
		frm.set_value("change_employment_status", "Regular");
	},

	regularization_type: function(frm) {
		frm.trigger("get_probationary");
	},

	get_probationary: function(frm) {
		if (frm.doc.regularization_type == "Probationary"){
			frm.set_value("change_employment_status", "Probationary");
		}
		if (frm.doc.regularization_type == ""){
			frm.set_value("change_employment_status", "Regular");
		}
	},

	filter_employees: function(frm) {
		//Filter Employee
		if (frm.doc.movement_type == "Job Rotation" || frm.doc.movement_type == "Retirement" || frm.doc.movement_type == "Resignation" || frm.doc.movement_type == "Regularization" || frm.doc.movement_type == "Transfer" || frm.doc.movement_type == "Termination" || frm.doc.movement_type == "Salary Adjustment" || frm.doc.movement_type == "Extension of Services" ){
			cur_frm.set_query("employee", function() {
				return {
					"filters": {
						"is_active": 1,
					}
				};
			});
		}else if (frm.doc.movement_type == "Rehire"){
			cur_frm.set_query("employee", function() {
				return {
					"filters": {
						"is_active": 0,
					}
				};
			});
		}else{
			cur_frm.set_query("employee", function() {
				return {
					"filters": {}
				};
			});
		}
	},
});
