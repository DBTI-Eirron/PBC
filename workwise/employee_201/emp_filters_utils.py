from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _

def empget_employees(filter_type, filter_value, company):
	employees = ""
	if filter_type == 'Employee':
		employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE is_active = 1 AND company = %(company)s  AND `name` = %(filter_value)s ORDER BY last_name, first_name""",{ 
			"company": company,
			"filter_value": filter_value,
		}, as_dict=True)
	
	elif filter_type == 'Department':
		employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE is_active = 1 AND company = %(company)s  AND department = %(filter_value)s ORDER BY last_name, first_name""",{ 
			"company": company,
			"filter_value": filter_value,
		}, as_dict=True)
	
	elif filter_type == 'Location':
		employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE is_active = 1 AND company = %(company)s  AND location = %(filter_value)s ORDER BY last_name, first_name""",{ 
			"company": company,
			"filter_value": filter_value,
		}, as_dict=True)

	elif filter_type == 'Job Level':
		employees = frappe.db.sql("""SELECT `name`, `full_name` FROM tabEmployee WHERE is_active = 1 AND company = %(company)s  AND job_level = %(filter_value)s ORDER BY last_name, first_name""",{ 
			"company": company,
			"filter_value": filter_value,
		}, as_dict=True)

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