# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	employee_list = get_employees(filters)

	from_date, to_date = frappe.db.get_value("Payroll Year", filters.year, ["from_date", "to_date"])
	periods = frappe.db.sql_list("""SELECT `name`
	 	FROM `tabPayroll Period` WHERE company = %(company)s
		AND payroll_date >= %(from_date)s
		AND payroll_date <= %(to_date)s ORDER BY payroll_date""",{ 
			"company": filters.company,
			"from_date": getdate(from_date),
			"to_date": getdate(to_date)
		})
	
	columns = get_columns(employee_list, periods)

	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list

	period_map = get_period_map(filters, employee_list, from_date, to_date)

	data = []
	for emp in employee_list:
		row = [emp.name, emp.full_name]

		total_grosspay = 0
		for p in periods:
			period_amount = flt(period_map.get(emp.name, {}).get(p))
			total_grosspay += period_amount
			row.append('{:,.2f}'.format(period_amount))
		row += ['{:,.2f}'.format(total_grosspay)]
		data.append(row)

	return columns, data

def get_columns(employee_list, periods):
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

	for row in periods:
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
			AND company = %(company)s ORDER BY last_name, first_name""",{ 
				"company": filters.company,
				"user": frappe.session.user
			}, as_dict=True)
	else:
		employees = frappe.db.sql("""SELECT `name`, full_name, first_name, middle_name, last_name, sensitivity
		 	FROM tabEmployee
			WHERE sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
				INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
			AND company = %(company)s ORDER BY last_name, first_name""",{ 
				"company": filters.company
			}, as_dict=True)

	return employees
	
def get_period_map(filters, employee_list, from_date, to_date):
	period_details = frappe.db.sql(""" SELECT PR.employee, PR.posting_date, PR.gross_payroll, PR.period
		FROM `tabPayroll Register` PR
		WHERE PR.posting_date >= %s AND PR.posting_date <= %s AND PR.company = (%s) AND PR.employee in (%s) GROUP BY PR.`name` """ %
		 ('%s','%s','%s',', '.join(['%s']*len(employee_list))), tuple([from_date, to_date, filters.company] + [emp.name for emp in employee_list]), as_dict=1)

	period_map = {}
	for d in period_details:
		period_map.setdefault(d.employee, frappe._dict()).setdefault(d.period, [])
		if period_map[d.employee][d.period]:
			period_map[d.employee][d.period] += flt(d.gross_payroll, 2)
		else:
			period_map[d.employee][d.period] = flt(d.gross_payroll, 2)

	return period_map