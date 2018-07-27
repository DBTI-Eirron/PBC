# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	validate_filters(filters)

	employee_list = get_employees(filters)
	columns, plus_types, less_types, tax_types	 = get_columns(employee_list)

	if not employee_list:
		msgprint(_("No record found"))
		return columns, employee_list

	plus_map = get_plus_map(filters, employee_list)
	less_map = get_less_map(filters, employee_list)
	tax_map = get_tax_map(filters, employee_list)

	data = []
	for emp in employee_list:
		total_gross = 0
		total_plus = 0
		total_less = 0
		total_tax = 0
		tax_due = 0

		row = [emp.tin, emp.name, emp.full_name]
		for plus in plus_types:
			plus_amount = flt(plus_map.get(emp.name, {}).get(plus), 2)
			total_plus += flt(plus_amount, 2)
			row.append(plus_amount)

		for less in less_types:
			less_amount = flt(less_map.get(emp.name, {}).get(less), 2)
			total_less += flt(less_amount, 2)
			row.append(less_amount)

		for tax in tax_types:
			tax_amount = flt(tax_map.get(emp.name, {}).get(tax), 2)
			total_tax += flt(tax_amount, 2)
		
		gross_compensation = flt(total_plus, 2) - flt(total_less, 2)
		
		table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table` 
			WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",(total_plus, total_plus, 'Yearly'), as_dict=True )

		for t in table:
			tax_due = (flt(taxable, 8) - flt(t.compensatory ,8)) * flt(flt(t.percentage, 8) / 100 , 8)

		adjustment, refund = get_adjustment(tax_due, total_tax)
		row.insert(2 , gross_compensation)
		row += [total_plus, total_less, tax_due, total_tax ,adjustment, refund, tax_due]

		data.append(row)

	return columns, data

def get_adjustment(tax_due, total_tax):
	adjustment, refund = 0, 0

	amt = tax_due - total_tax
	if amt > 0:
		refund = abs(amt)
	else:
		adjustment = abs(amt)

	return adjustment, refund


def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

def get_columns(employee_list):
	columns = [
		{
			"fieldname": "tin",
			"label": _("TIN"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "gross_payroll",
			"label": _("Gross Payroll"),
			"fieldtype": "Currency",
			"width": 100
		},
	]

	if employee_list:
		plus_types = frappe.db.sql_list(""" SELECT `name`
			FROM `tabAlphalist Consideration` WHERE `calculation` = 'Plus' """)

		less_types = frappe.db.sql_list(""" SELECT `name`
			FROM `tabAlphalist Consideration` WHERE `calculation` = 'Less' """)

		tax_types = frappe.db.sql_list(""" SELECT `name`
			FROM `tabAlphalist Consideration` WHERE `calculation` = 'Tax' """)


	for plus in plus_types:
		columns.append({			
			"fieldname": plus,
			"label": plus,
			"fieldtype": "Float",
			"width": 100
		})

	for less in less_types:
		columns.append({			
			"fieldname": less,
			"label": less,
			"fieldtype": "Float",
			"width": 100
		})

	columns += [
		{
			"fieldname": "taxable_compensation",
			"label": _("Taxable Compensation"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "exemption_amount",
			"label": _("Exemption Amount"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "tax_due",
			"label": _("Tax Due"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "tax_withheld",
			"label": _("Tax Withheld"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "adjustment",
			"label": _("Adjustment Amount"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "refund",
			"label": _("Refunded Amount"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "adj_tax_withheld",
			"label": _("Amount  of Tax Withheld"),
			"fieldtype": "Float",
			"width": 100
		},
	]

	return columns, plus_types, less_types, tax_types

def get_employees(filters):
	employees = frappe.db.sql("""SELECT `name`, full_name, first_name, middle_name, last_name, tin	FROM tabEmployee
		WHERE company = %(company)s {conditions}
		AND on_hold = 0 AND is_active = 1 ORDER BY last_name, first_name""".format(conditions=get_conditions(filters)), filters, as_dict=1)

	return employees

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 

def get_plus_map(filters, employee_list):
	plus_details = frappe.db.sql("""SELECT PR.employee, PR.posting_date, AC.`name` as alpha_code, SUM(PRE.amount) as amount
			FROM `tabPayroll Register` PR 
			INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent`
			INNER JOIN `tabTransaction Type` TT ON TT.`name` = PRE.pay_code
			INNER JOIN `tabAlphalist Consideration` AC ON AC.`name` = TT.alphalist
			WHERE AC.calculation = 'Plus'
			AND year(posting_date) = %s AND employee in (%s) GROUP BY PRE.`name` """ %
		('%s',', '.join(['%s']*len(employee_list))), tuple([filters.year] + [emp.name for emp in employee_list]), as_dict=1)

	plus_map = {}
	for d in plus_details:
		plus_map.setdefault(d.employee, frappe._dict()).setdefault(d.alpha_code, [])
		if plus_map[d.employee][d.alpha_code]:
			plus_map[d.employee][d.alpha_code] += flt(d.amount, 8)
		else:
			plus_map[d.employee][d.alpha_code] = flt(d.amount, 8)

	return plus_map

def get_less_map(filters, employee_list):
	less_details = frappe.db.sql("""SELECT PR.employee, PR.posting_date, AC.`name` as alpha_code, SUM(PRE.amount) as amount
			FROM `tabPayroll Register` PR 
			INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent`
			INNER JOIN `tabTransaction Type` TT ON TT.`name` = PRE.pay_code
			INNER JOIN `tabAlphalist Consideration` AC ON AC.`name` = TT.alphalist
			WHERE AC.calculation = 'Less'
			AND year(posting_date) = %s AND employee in (%s) GROUP BY PRE.`name` """ %
		('%s',', '.join(['%s']*len(employee_list))), tuple([filters.year] + [emp.name for emp in employee_list]), as_dict=1)

	less_map = {}
	for d in less_details:
		less_map.setdefault(d.employee, frappe._dict()).setdefault(d.alpha_code, [])
		if less_map[d.employee][d.alpha_code]:
			less_map[d.employee][d.alpha_code] += flt(d.amount, 8)
		else: 
			less_map[d.employee][d.alpha_code] = flt(d.amount, 8)

	return  less_map

def get_tax_map(filters, employee_list):
	tax_details = frappe.db.sql("""SELECT PR.employee, PR.posting_date, AC.`name` as alpha_code, SUM(PRE.amount) as amount
			FROM `tabPayroll Register` PR 
			INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent`
			INNER JOIN `tabTransaction Type` TT ON TT.`name` = PRE.pay_code
			INNER JOIN `tabAlphalist Consideration` AC ON AC.`name` = TT.alphalist
			WHERE AC.calculation = 'Tax'
			AND year(posting_date) = %s AND employee in (%s) GROUP BY PRE.`name` """ %
		('%s',', '.join(['%s']*len(employee_list))), tuple([filters.year] + [emp.name for emp in employee_list]), as_dict=1)

	tax_map = {}
	for d in tax_details:
		tax_map.setdefault(d.employee, frappe._dict()).setdefault(d.alpha_code, [])
		if tax_map[d.employee][d.alpha_code]:
			tax_map[d.employee][d.alpha_code] += flt(d.amount, 8)
		else: 
			tax_map[d.employee][d.alpha_code] = flt(d.amount, 8)

	return  tax_map