# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr
from frappe import _

def execute(filters=None):
	validate_filters(filters)
	columns = get_columns(filters)
	result = get_result(filters)
	return columns, result

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)
	return result

def get_columns(filters):
	columns = [
		_("ID") + "::200",
		_("Fullname") + "::120",
	]

	return columns


def validate_filters(filters):
	if filters.emp_name == 'ivy':
		frappe.throw(_("Error"))

	if filters.emp_name == 'chie':
		frappe.throw(_("Error 2"))

def get_data(filters):

	entries = frappe.db.sql("""SELECT `name`, full_name FROM tabEmployee  """.format(conditions=get_conditions(filters)), filters, as_dict=1)

	return entries

def get_conditions(filters):
	conditions = []

	#if filters.get("company"):
	#	conditions.append("company=%(company)s")

	#if filters.get("emp_name"):
	#	emp_name = filters.get("emp_name")
	#	conditions.append("full_name LIKE '%%"+emp_name+"%%' ")
	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = [
			d.get("name"),
			d.get("full_name"),
		]

		result.append(row)

	return result
