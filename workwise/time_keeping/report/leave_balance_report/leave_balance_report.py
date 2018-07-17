# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import date
from frappe import _
from frappe.utils import getdate

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "leave_balance",
			"label": _("Leave Balance"),
			"fieldtype": "Link",
			"options": "Leave Balance",
			"width": 130
		},
		{
			"fieldname": "leave_type",
			"label": _("Leave Type"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "credits",
			"label": _("Credits"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "used_credits",
			"label": _("Used Credits"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "balance",
			"label": _("Balance"),
			"fieldtype": "Data",
			"width": 130
		},
	]

	return columns

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_data(filters):
	#Initialize
	data = []

	if filters.year:
		from_date, to_date = frappe.db.get_value("Payroll Year", filters.year, ["attendance_from", "attendance_to"])
		employees = get_employees(filters)
		for emp in employees:
			leave_balance = frappe.db.sql(""" SELECT `employee_name`,`from_date`,`name`,`leave_type`,`credits`,`used_credits`,`credits`-`used_credits` as balance FROM `tabLeave Balance` WHERE `employee`=%s AND `to_date` <= %s AND `from_date` >= %s """, (emp.name, to_date, from_date),as_dict=True)
			for leave in leave_balance:
				entry = {
					"employee": leave.employee_name,
					"leave_balance": leave.name,
					"leave_type": leave.leave_type,
					"credits": leave.credits,
					"used_credits": leave.used_credits,
					"balance": leave.balance,
				}
				data.append(entry)
				
	if filters.from_date or filters.to_date:
		if not filters.to_date:
			frappe.throw(_("To Date is required"))

		if not filters.from_date:
			frappe.throw(_("From Date is required"))
		
		from_date = filters.from_date
		to_date = filters.to_date
		employees = get_employees(filters)
		for emp in employees:
			leave_balance = frappe.db.sql(""" SELECT `employee_name`,`from_date`,`name`,`leave_type`,`credits`,`used_credits`,`credits`-`used_credits` as balance FROM `tabLeave Balance` WHERE `employee`=%s AND `to_date` <= %s """, (emp.name, to_date),as_dict=True)
			for leave in leave_balance:
				#if getdate(leave.from_date) >= getdate(filters.from_date): 
					#frappe.throw(_(leave.from_date))
				entry = {
					"employee": leave.employee_name,
					"leave_balance": leave.name,
					"leave_type": leave.leave_type,
					"credits": leave.credits,
					"used_credits": leave.used_credits,
					"balance": leave.balance,
				}
				data.append(entry)

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)
	return result

def get_employees(filters):
	register = frappe.db.sql("""SELECT `name`, full_name FROM `tabEmployee` 
		WHERE company = %(company)s {conditions}""".format(conditions=get_conditions(filters)), filters, as_dict=1)

	return register

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 