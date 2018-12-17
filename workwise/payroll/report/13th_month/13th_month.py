# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	employee_list = get_employees(filters)

	columns = get_columns(employee_list)

	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list

	total_amount = 0.0	

	data = []
	for emp in employee_list:
		pay = get_data(filters, emp)
		row = [emp.employee, emp.employee_name, '{:,.2f}'.format(pay[0].amount)]
		total_amount += flt(pay[0].amount, 8)

		data.append(row)	
	data.append(["<b>Total</b>", "", '{:,.2f}'.format(total_amount)])

	return columns, data

def get_columns(employee_list):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 160
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 260
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Float",
			"width": 160
		}
	]

	return columns

def get_employees(filters):
	from_date, to_date = frappe.db.get_value("Payroll Year", filters.year, ["from_date", "to_date"])
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql("""SELECT DISTINCT PE.employee, PE.employee_name
			FROM `tabBatch Entry` PR JOIN `tabBatch Entry Employees` PE ON PR.`name` = PE.parent JOIN `tabEmployee` TE ON PR.employee = TE.`name` 
			WHERE PR.transaction_type = "13TH_BONUS" 
			AND PR.company = %(company)s 
			AND PR.period IN (SELECT `name` FROM `tabPayroll Period` WHERE payroll_date >= %(from_date)s AND payroll_date <= %(to_date)s)
			AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(user)s) """, { 
				"from_date": from_date,
				"to_date": to_date,
				"company": filters.company,
				"user": cur_user
			}, as_dict=1)
	else:
		employees = frappe.db.sql("""SELECT DISTINCT PE.employee, PE.employee_name
			FROM `tabBatch Entry` PR JOIN `tabBatch Entry Employees` PE ON PR.`name` = PE.parent 
			WHERE PR.transaction_type = "13TH_BONUS" AND PR.company = %(company)s AND PR.period IN (SELECT `name` FROM `tabPayroll Period` WHERE payroll_date >= %(from_date)s AND payroll_date <= %(to_date)s)""", { 
				"from_date": from_date,
				"to_date": to_date,
				"company": filters.company
			}, as_dict=1)

	return employees


def get_data(filters, emp):
	from_date, to_date = frappe.db.get_value("Payroll Year", filters.year, ["from_date", "to_date"])

	data_entry = frappe.db.sql("""SELECT DISTINCT SUM(PE.amount) as amount
		FROM `tabBatch Entry` PR JOIN `tabBatch Entry Employees` PE ON PR.`name` = PE.parent
		WHERE PR.transaction_type = "13TH_BONUS" 
		AND PR.company = %(company)s 
		AND PR.period IN (SELECT `name` FROM `tabPayroll Period` WHERE payroll_date >= %(from_date)s AND payroll_date <= %(to_date)s)
		AND PE.employee = %(employee)s """, { 
			"from_date": from_date,
			"to_date": to_date,
			"company": filters.company,
			"employee": emp.employee
		}, as_dict=1)


	return data_entry