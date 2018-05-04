from __future__ import unicode_literals

import frappe
from frappe import _

def empget_employees(filter_type, filter_value, company):
	employees = ""
	select_fields = """ `name`, full_name, company  """ 
	conditions = []
	if filter_type == 'Employee':
		conditions.append("`name`=%(filter_value)s")

	if filter_type == 'Department':
		conditions.append("department=%(filter_value)s")

	if filter_type == 'Location':
		conditions.append("`name`=%(filter_value)s")

	build_conditions = "and {}".format(" and ".join(conditions)) if conditions else "" 

	if filter_value:
		employees = frappe.db.sql("""SELECT {select_fields} FROM tabEmployee WHERE company = %(company)s {conditions} ORDER BY last_name, first_name""".format(conditions=build_conditions, select_fields=select_fields),{ 
			"company": company,
			"filter_value": filter_value,
		}, as_dict=1)
	
	return employees

def empget_subordinates(cur_user):
	emp = frappe.db.sql(""" SELECT `name` FROM `tabEmployee` WHERE user_id = %s LIMIT 1""",(cur_user))
	emp = emp[0][0] if emp else ""
	employees = frappe.db.sql(""" SELECT SB.subordinate as `name`, SB.subordinate_name as full_name FROM `tabEmployee Subordinates` ES 
		INNER JOIN `tabSubordinates` SB ON ES.employee = SB.parent 
		WHERE ES.employee = %s """,(emp), as_dict=True)
	return employees

def empget_company(company):
	employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s ORDER BY last_name, first_name""",{ 
		"company": company,
	}, as_dict=True)

	return employees

def empget_managers(company):
	employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE company = %(company)s ORDER BY last_name, first_name""",{ 
		"company": company,
	}, as_dict=True)

	return employees