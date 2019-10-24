# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_columns(employee_list):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 140
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee name"),
			"fieldtype": "Data",
			"width": 160
		},
		{
			"fieldname": "income_absent",
			"label": _("Income Absent"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "deduction_absent",
			"label": _("Deduction Absent"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "income_uh",
			"label": _("Income Unpaid Holiday"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "deduction_uh",
			"label": _("Deduction Unpaid Holiday"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "income_ot",
			"label": _("Income Overtime"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "deduction_ot",
			"label": _("Deduction Overtime"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "income_nd",
			"label": _("Income Nightdiff"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "deduction_nd",
			"label": _("Deduction Nightdiff"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "income_late",
			"label": _("Income Late"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "deduction_late",
			"label": _("Deduction Late"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "income_ut",
			"label": _("Income Undertime"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "deduction_ut",
			"label": _("Deduction Undertime"),
			"fieldtype": "Data",
			"width": 140
		},
	]

	return columns

def get_data(filters):
	data = []
	
	register = frappe.db.sql("""SELECT * FROM `tabAdjustment Register` 
		WHERE `company` = %(company)s AND `target_period` = %(payroll_period)s {conditions}
		ORDER BY `employee_name` ASC""".format(conditions=get_conditions(filters)),{
		"company": filters.company,
		"employee": filters.employee,
		"payroll_period": filters.payroll_period,
	}, as_dict=True)

	if register:
		for reg in register:
			income_absent = 0
			deduction_absent = 0
			income_uh = 0
			deduction_uh = 0
			income_ot = 0
			deduction_ot = 0
			income_nd = 0
			deduction_nd = 0
			income_late = 0
			deduction_late = 0
			income_ut = 0
			deduction_ut = 0

			if reg.absent < 0:
				income_absent = flt(abs(reg.absent))
			else:
				deduction_absent = flt(abs(reg.absent))

			if reg.unpaid_holiday < 0:
				income_uh = flt(abs(reg.unpaid_holiday))
			else:
				deduction_uh = flt(abs(reg.unpaid_holiday))

			if reg.overtime < 0:
				deduction_ot = flt(abs(reg.overtime))
			else:
				income_ot = flt(abs(reg.overtime))

			if reg.nightdiff < 0:
				deduction_nd = flt(abs(reg.nightdiff))
			else:
				income_nd = flt(abs(reg.nightdiff))

			if reg.late < 0:
				income_late = flt(abs(reg.late))
			else:
				deduction_late = flt(abs(reg.late))

			if reg.undertime < 0:
				income_ut = flt(abs(reg.undertime))
			else:
				deduction_ut = flt(abs(reg.undertime))

			if filters.hide_zero == 1:
				emp_total = flt(income_absent) + flt(deduction_absent) + flt(income_uh) + flt(deduction_uh) + flt(income_ot) + flt(deduction_ot) + flt(income_nd) + flt(deduction_nd) + flt(income_late) + flt(deduction_late) + flt(income_ut) + flt(deduction_ut)
				if emp_total > 1:
					row = {
						"employee": reg.employee,
						"employee_name": reg.employee_name,
						"income_absent": '{:,.2f}'.format(income_absent),
						"deduction_absent": '{:,.2f}'.format(deduction_absent),
						"income_uh": '{:,.2f}'.format(income_uh),
						"deduction_uh": '{:,.2f}'.format(deduction_uh),
						"income_ot": '{:,.2f}'.format(income_ot),
						"deduction_ot": '{:,.2f}'.format(deduction_ot),
						"income_nd": '{:,.2f}'.format(income_nd),
						"deduction_nd": '{:,.2f}'.format(deduction_nd),
						"income_late": '{:,.2f}'.format(income_late),
						"deduction_late": '{:,.2f}'.format(deduction_late),
						"income_ut": '{:,.2f}'.format(income_ut),
						"deduction_ut": '{:,.2f}'.format(deduction_ut),
					}
					data.append(row)
			else:
				row = {
					"employee": reg.employee,
					"employee_name": reg.employee_name,
					"income_absent": '{:,.2f}'.format(income_absent),
					"deduction_absent": '{:,.2f}'.format(deduction_absent),
					"income_uh": '{:,.2f}'.format(income_uh),
					"deduction_uh": '{:,.2f}'.format(deduction_uh),
					"income_ot": '{:,.2f}'.format(income_ot),
					"deduction_ot": '{:,.2f}'.format(deduction_ot),
					"income_nd": '{:,.2f}'.format(income_nd),
					"deduction_nd": '{:,.2f}'.format(deduction_nd),
					"income_late": '{:,.2f}'.format(income_late),
					"deduction_late": '{:,.2f}'.format(deduction_late),
					"income_ut": '{:,.2f}'.format(income_ut),
					"deduction_ut": '{:,.2f}'.format(deduction_ut),
				}
				data.append(row)
	return data

def get_conditions(filters):
	conditions = []
	if filters.employee:
		conditions.append("`employee` = %(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 





