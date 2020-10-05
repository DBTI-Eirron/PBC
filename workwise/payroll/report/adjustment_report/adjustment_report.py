# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters, columns)

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
		{
			"fieldname": "income_cto",
			"label": _("Income CTO"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "deduction_cto",
			"label": _("Deduction CTO"),
			"fieldtype": "Data",
			"width": 140
		},
	]

	return columns

def get_data(filters, columns):
	data = []
	
	register = frappe.db.sql("""SELECT * FROM `tabAdjustment Register` 
		WHERE `company` = %(company)s AND `target_period` = %(payroll_period)s {conditions}
		ORDER BY `employee_name` ASC""".format(conditions=get_conditions(filters)),{
		"company": filters.company,
		"employee": filters.employee,
		"payroll_period": filters.payroll_period,
	}, as_dict=True)

	if register:
		totals = {
			"total_income_absent": 0,
			"total_deduction_absent": 0,
			"total_income_uh": 0,
			"total_deduction_uh": 0,
			"total_income_ot": 0,
			"total_deduction_ot": 0,
			"total_income_nd": 0,
			"total_deduction_nd": 0,
			"total_income_late": 0,
			"total_deduction_late": 0,
			"total_income_ut": 0,
			"total_deduction_ut": 0,
			"total_income_cto": 0,
			"total_deduction_cto": 0,
		}

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
			income_cto = 0
			deduction_cto = 0

			if reg.absent < 0:
				income_absent = flt(abs(reg.absent))
				totals['total_income_absent'] += flt(abs(reg.absent))
			else:
				deduction_absent = flt(abs(reg.absent))
				totals['total_deduction_absent'] += flt(abs(reg.absent))

			if reg.unpaid_holiday < 0:
				income_uh = flt(abs(reg.unpaid_holiday))
				totals['total_income_uh'] += flt(abs(reg.unpaid_holiday))
			else:
				deduction_uh = flt(abs(reg.unpaid_holiday))
				totals['total_deduction_uh'] += flt(abs(reg.unpaid_holiday))

			if reg.overtime < 0:
				deduction_ot = flt(abs(reg.overtime))
				totals['total_deduction_ot'] += flt(abs(reg.overtime))
			else:
				income_ot = flt(abs(reg.overtime))
				totals['total_income_ot'] += flt(abs(reg.overtime))

			if reg.nightdiff < 0:
				deduction_nd = flt(abs(reg.nightdiff))
				totals['total_deduction_nd'] += flt(abs(reg.nightdiff))
			else:
				income_nd = flt(abs(reg.nightdiff))
				totals['total_income_nd'] += flt(abs(reg.nightdiff))

			if reg.late < 0:
				income_late = flt(abs(reg.late))
				totals['total_income_late'] += flt(abs(reg.late))
			else:
				deduction_late = flt(abs(reg.late))
				totals['total_deduction_late'] += flt(abs(reg.late))

			if reg.undertime < 0:
				income_ut = flt(abs(reg.undertime))
				totals['total_income_ut'] += flt(abs(reg.undertime))
			else:
				deduction_ut = flt(abs(reg.undertime))
				totals['total_deduction_ut'] += flt(abs(reg.undertime))

			if reg.compensatory < 0:
				deduction_cto = flt(abs(reg.compensatory))
				totals['total_deduction_cto'] += flt(abs(reg.compensatory))
			else:
				income_cto = flt(abs(reg.compensatory))
				totals['total_income_cto'] += flt(abs(reg.compensatory))

			emp_total = flt(income_absent) + flt(deduction_absent) + flt(income_uh) + flt(deduction_uh) + flt(income_ot) + flt(deduction_ot) + flt(income_nd) + flt(deduction_nd) + flt(income_late) + flt(deduction_late) + flt(income_ut) + flt(deduction_ut)+ flt(income_cto) + flt(deduction_cto)
			if emp_total > 1:
				row = {
					"employee": reg.employee,
					"employee_name": reg.employee_name,
					"income_absent": format_precision(income_absent, filters.value_precision),
					"deduction_absent": format_precision(deduction_absent, filters.value_precision),
					"income_uh": format_precision(income_uh, filters.value_precision),
					"deduction_uh": format_precision(deduction_uh, filters.value_precision),
					"income_ot": format_precision(income_ot, filters.value_precision),
					"deduction_ot": format_precision(deduction_ot, filters.value_precision),
					"income_nd": format_precision(income_nd, filters.value_precision),
					"deduction_nd": format_precision(deduction_nd, filters.value_precision),
					"income_late": format_precision(income_late, filters.value_precision),
					"deduction_late": format_precision(deduction_late, filters.value_precision),
					"income_ut": format_precision(income_ut, filters.value_precision),
					"deduction_ut": format_precision(deduction_ut, filters.value_precision),
					"income_cto": format_precision(income_cto, filters.value_precision),
					"deduction_cto": format_precision(deduction_cto, filters.value_precision),
				}
				data.append(row)
			
		if filters.hide_zero == 1:
			i = 2
			for tot in ["total_income_absent", "total_deduction_absent", "total_income_uh", "total_deduction_uh", "total_income_ot", "total_deduction_ot", "total_income_nd", "total_deduction_nd", "total_income_late", "total_deduction_late", "total_income_ut", "total_deduction_ut", "total_income_cto", "total_deduction_cto"]:
				if totals[tot] < 1:
					del columns[i]
					for d in data:	
						del d[cstr(tot)[6:]]
					i -= 1
				i += 1

	return data

def get_conditions(filters):
	conditions = []
	if filters.employee:
		conditions.append("`employee` = %(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 





