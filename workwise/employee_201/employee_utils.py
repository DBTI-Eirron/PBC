# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def set_employee_name(doc):
	if frappe.session.user:
		frappe.db.get_value("Employee", doc.employee, "full_name")

def tool_insert_approvers():
	employees = frappe.db.sql("""select `name` FROM tabEmployee  """, as_dict=1)
	approvers = frappe.db.sql("""select employee, employee_name, level, approver, approver_name, approver_userid FROM `tempApprovers`  """, as_dict=1)

	emp_map = frappe._dict()
	for emp in employees:
		emp_map.setdefault(emp.name, frappe._dict({
				"name": emp.name,
				"approvers": [],
			})
		)

	for ap in approvers:
		if ap.employee in emp_map:
			emp_map[ap.employee].approvers.append(ap)

	app_list = ["Leave Application", "Overtime Application", "Official Business Application", "Change Schedule Application", "Undertime Application", "DTR Problem Application"]
	for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['name']):
		per_emp_approvers = []
		for apr in emp_dict['approvers']:
			per_emp_approvers.append(apr)

		for apl in app_list:
			for d in per_emp_approvers: 
				employee_data = frappe.get_doc("Employee", emp)
				employee_data.append("approvers", {
					"approver": cstr(d.approver),
					"approver_name": cstr(d.approver_name),
					"approver_userid": cstr(d.approver_userid),	
					"application": cstr(apl),
					"level": cstr(d.level),
				})
				employee_data.save()
				frappe.db.commit()
	print("Done")

def tool_insert_cto_approvers():
	employees = frappe.db.sql("""select `name` FROM tabEmployee WHERE (job_level = 'Manager' or job_level = 'Officer') """, as_dict=1)
	approvers = frappe.db.sql("""select employee, employee_name, level, approver, approver_name, approver_userid FROM `tempApprovers`  """, as_dict=1)

	emp_map = frappe._dict()
	for emp in employees:
		emp_map.setdefault(emp.name, frappe._dict({
				"name": emp.name,
				"approvers": [],
			})
		)

	for ap in approvers:
		if ap.employee in emp_map:
			emp_map[ap.employee].approvers.append(ap)

	app_list = ["Compensatory Time Off"]
	for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['name']):
		per_emp_approvers = []
		for apr in emp_dict['approvers']:
			per_emp_approvers.append(apr)

		for apl in app_list:
			for d in per_emp_approvers: 
				employee_data = frappe.get_doc("Employee", emp)
				employee_data.append("approvers", {
					"approver": cstr(d.approver),
					"approver_name": cstr(d.approver_name),
					"approver_userid": cstr(d.approver_userid),	
					"application": cstr(apl),
					"level": cstr(d.level),
				})
				employee_data.save()
				frappe.db.commit()

	print("Done")

def tool_check_emp_consistency():
	employees = frappe.db.sql("""select `name` FROM tabEmployee  """, as_dict=1)
	for emp in employees:
		employee_data = frappe.get_doc("Employee", emp)
		employee_data.save()
		frappe.db.commit()

	print("Complete")
