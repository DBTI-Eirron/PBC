# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe, datetime, calendar
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	employee_dict, employee_list = get_employees(filters)
	from_date, to_date = "", ""
	months = [ "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December" ]
	
	columns = get_columns(employee_list, months)

	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list

	data = []
	total_row = {
		'employee': '<b>Total</b>',
		'employee_name': "",
		'net_pay': 0.00,
	}
	for emp in employee_list:
		month_count = 0

		row = {
			'employee': emp,
			'employee_name': frappe.db.get_value("Employee", emp, "full_name"),
		}

		total_grosspay = 0
		for p in months:
			period_amount = 0
			month_count += 1
			from_date = str(filters.year)+"-"+str(month_count)+"-01"
			to_date = str(filters.year)+"-"+str(month_count)+"-"+str(calendar.monthrange(int(filters.year), int(month_count))[1])
			for reg in employee_dict[emp]:
				if getdate(reg['posting_date']) >= getdate(from_date) and getdate(reg['posting_date']) <= getdate(to_date):
					if reg['gross_payroll'] > 0:
						period_amount += flt(reg['gross_payroll'], 2)
					
			total_grosspay += period_amount
			row[p] = format_precision(period_amount, filters.value_precision)

			if p not in total_row:
				total_row[p] = 0.00
			total_row[p] += period_amount

		row['net_pay'] = format_precision(total_grosspay, filters.value_precision)
		total_row['net_pay'] += total_grosspay
		data.append(row)

	for pm in months:
		total_row[pm] = format_precision(total_row[pm], filters.value_precision)
	total_row['net_pay'] = format_precision(total_row['net_pay'], filters.value_precision)
	data.append(total_row)

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
				"fieldtype": "Data",
				"width": 170
		}]	

	columns += [{
			"fieldname": "net_pay",
			"label": _("Total "),
			"fieldtype": "Data",
			"width": 100
		}]

	return columns

def get_employees(filters):
	employee_list = []
	employee_dict = {}

	from_date = str(filters.year)+"-01-01"
	to_date = str(filters.year)+"-12-"+str(calendar.monthrange(int(filters.year), 12)[1])

	employees = frappe.db.sql(""" SELECT PR.employee, PR.employee_name, PR.posting_date, PR.gross_payroll, PR.period 
		FROM `tabPayroll Register` PR 
		INNER JOIN `tabEmployee` TE ON PR.`employee`=TE.`name`
		INNER JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name`
		WHERE PR.company = %(company)s AND PR.on_hold = 0
		AND (PR.posting_date >= %(from_date)s AND PR.posting_date <= %(to_date)s)
		{conditions} ORDER BY TE.full_name """.format(conditions=get_conditions(filters)), { 
			'from_date': str(getdate(from_date)),
			'to_date': str(getdate(to_date)),
			'company': filters.company,
			'employee': filters.employee,
		}, as_dict=True)

	for emp in employees:
		if emp.employee not in employee_list:
			employee_list.append(emp.employee)

		if emp.employee not in employee_dict:
			employee_dict[emp.employee] = []
		employee_dict[emp.employee].append(emp)

	return employee_dict, employee_list
	
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
	if frappe.session.user != "Administrator":
		conditions.append(_("TE.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

	if filters.employee:
		conditions.append("PR.`employee`=%(employee)s")

	if filters.get("department"):
		lft, rgt = frappe.db.get_value("Department", filters.department, ["lft", "rgt"])
		conditions.append(_("( DEPT.`lft` BETWEEN '{0}' AND '{1}' )").format(lft, rgt))

	return "AND {}".format(" AND ".join(conditions)) if conditions else ""