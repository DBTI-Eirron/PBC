# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime, dateutil
from datetime import date  
from frappe.utils import cint, flt, getdate, cstr
from frappe import _
from workwise.payroll.payroll_utils import format_decimal_by_2

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100
		},
		{
			"fieldname": "last_name",
			"label": _("Last Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "first_name",
			"label": _("First Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "middle_name",
			"label": _("Middle Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "position_title",
			"label": _("Position"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "date_hired",
			"label": _("Date Hired"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rate",
			"label": _("Rate"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "address_html",
			"label": _("Address"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "birthday",
			"label": _("Birthday"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "age",
			"label": _("Age"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "birth_place",
			"label": _("Birth Place"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "sss_no",
			"label": _("SSS Number"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "hdmf_no",
			"label": _("HDMF Number"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "tin",
			"label": _("TIN Number"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "phic_no",
			"label": _("PHIC Number"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "gender",
			"label": _("Gender"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "civil_status",
			"label": _("Civil Status"),
			"fieldtype": "Data",
			"width": 100
		},
	]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_employees(filters):
	employees = frappe.db.sql("""SELECT *
	 	FROM tabEmployee
		WHERE company = %(company)s
		AND on_hold = 0
		AND is_active = 1 ORDER BY last_name, first_name""",{ 
			"company": filters.company
	}, as_dict=True)

	return employees

def get_data(filters):
	data = []
	employees = get_employees(filters)

	for emp in employees: 
		data.append(emp)

	return data
 
def get_result_as_list(data, filters):
	cur_user = frappe.session.user
	result = []
	user_sensitivity = []
	sensitivy_user = frappe.db.sql(""" SELECT `parent` FROM `tabSensitivity Users` WHERE `allow_user` = %s""",( frappe.session.user ), as_dict=1)
	if sensitivy_user:
		for user in sensitivy_user:
			user_sensitivity.append(user.parent)

	for d in data:
		bday = d.get("birthday")
		if not "Administrator" in frappe.get_roles(cur_user):
			if d.get("sensitivity") in user_sensitivity:
				row = {
					"employee": d.get("name"),
					"last_name": d.get("last_name"),
					"first_name": d.get("first_name"),
					"middle_name": d.get("middle_name"),
					"position_title": d.get("position_title"),
					"date_hired": d.get("date_hired"),
					"address_html": d.get("address_html"),
					"birthday": d.get("birthday"),
					"age": calculate_age(bday),
					"birth_place": d.get("birth_place"),
					"gender": d.get("gender"),
					"civil_status": d.get("civil_status"),
					"rate": format_decimal_by_2(d.get("rate")),
					"sss_no": d.get("sss_no"),
					"hdmf_no": d.get("hdmf_no"),
					"tin": d.get("tin"),
					"phic_no": d.get("phic_no"),
				}
			else:
				row = {
					"employee": d.get("name"),
					"last_name": d.get("last_name"),
					"first_name": d.get("first_name"),
					"middle_name": d.get("middle_name"),
					"position_title": d.get("position_title"),
					"date_hired": d.get("date_hired"),
					"address_html": d.get("address_html"),
					"birthday": d.get("birthday"),
					"age": calculate_age(bday),
					"birth_place": d.get("birth_place"),
					"gender": d.get("gender"),
					"civil_status": d.get("civil_status"),
				}
		else:
			row = {
				"employee": d.get("name"),
				"last_name": d.get("last_name"),
				"first_name": d.get("first_name"),
				"middle_name": d.get("middle_name"),
				"position_title": d.get("position_title"),
				"date_hired": d.get("date_hired"),
				"address_html": d.get("address_html"),
				"birthday": d.get("birthday"),
				"age": calculate_age(bday),
				"birth_place": d.get("birth_place"),
				"gender": d.get("gender"),
				"civil_status": d.get("civil_status"),
				"rate": format_decimal_by_2(d.get("rate")),
				"sss_no": d.get("sss_no"),
				"hdmf_no": d.get("hdmf_no"),
				"tin": d.get("tin"),
				"phic_no": d.get("phic_no"),
			}

		result.append(row)

	

	return result

def calculate_age(dtob):
    today = date.today()
    return today.year - dtob.year - ((today.month, today.day) < (dtob.month, dtob.day))