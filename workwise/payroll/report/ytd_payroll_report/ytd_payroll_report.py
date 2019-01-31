# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe, datetime, calendar
from frappe.utils import cint, flt, getdate, cstr
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	employee_list = get_employees(filters)
	from_date, to_date = "", ""
	months = [ "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December" ]
	
	columns = get_columns(employee_list, months)

	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list

	data = []
	for emp in employee_list:
		month_count = 0
		row = [emp.name, emp.full_name]

		total_grosspay = 0
		for p in months:
			month_count += 1
			from_date = str(filters.year)+"-"+str(month_count)+"-01"
			to_date = str(filters.year)+"-"+str(month_count)+"-"+str(calendar.monthrange(int(filters.year), int(month_count))[1])

			period_amount = get_period_map(filters, emp.name, from_date, to_date)
			total_grosspay += period_amount
			row.append('{:,.2f}'.format(period_amount))
		row += ['{:,.2f}'.format(total_grosspay)]
		data.append(row)

	return columns, data

def get_columns(employee_list, months):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 220
		}]

	for row in months:
		columns += [{
				"fieldname": row,
				"label": row,
				"fieldtype": "Float",
				"width": 170
		}]	

	columns += [{
			"fieldname": "net_pay",
			"label": _("Total "),
			"fieldtype": "Float",
			"width": 100
		}]

	return columns

def get_employees(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql("""SELECT `name`, full_name, first_name, middle_name, last_name, sensitivity
		 	FROM tabEmployee
			WHERE sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
				INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`
				WHERE SU.allow_user = %(user)s)
			AND company = %(company)s {conditions} ORDER BY last_name, first_name""".format(conditions=get_conditions(filters)), { 
				"company": filters.company,
				"employee": filters.employee,
				"department": filters.department,
				"user": frappe.session.user
			}, as_dict=1)
	else:
		employees = frappe.db.sql("""SELECT `name`, full_name, first_name, middle_name, last_name, sensitivity
		 	FROM tabEmployee
			WHERE sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
				INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
			AND company = %(company)s {conditions} ORDER BY last_name, first_name""".format(conditions=get_conditions(filters)), { 
				"company": filters.company,
				"employee": filters.employee,
				"department": filters.department
			}, as_dict=1)

	return employees
	
def get_period_map(filters, emp, from_date, to_date):
	amount = 0.00
	period_details = frappe.db.sql(""" SELECT PR.employee, PR.posting_date, PR.gross_payroll, PR.period FROM `tabPayroll Register` PR 
		WHERE PR.posting_date >= %s AND PR.posting_date <= %s AND PR.company = %s AND PR.employee = %s """,(str(from_date), str(to_date), filters.company, emp ), as_dict=True)

	if period_details:
		for d in period_details:
			amount += flt(d.gross_payroll, 2)

	return amount

def get_conditions(filters):
	conditions = []
	if filters.employee:
		conditions.append("`name`=%(employee)s")

	if filters.department:
		conditions.append("`department`=%(department)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""