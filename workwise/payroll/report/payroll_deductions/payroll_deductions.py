# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _
from workwise.payroll.payroll_utils import get_transaction_map

def execute(filters=None):	
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "deduction_type",
			"label": _("Deduction Type"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "code",
			"label": _("Code"),
			"fieldtype": "Link",
			"options": "Transaction Type",
			"width": 130
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Float",
			"width": 130
		},
	]

	return columns

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_register(filters):
	register = frappe.db.sql("""SELECT PR.employee, PRE.pay_code, PRE.amount FROM `tabPayroll Register` PR
		INNER JOIN `tabPayroll Register Entries` PRE ON PRE.parent = PR.`name` 
		WHERE PR.period = %(period)s AND PRE.pay_type = "Deduction" {conditions} """.format(conditions=get_conditions(filters)), filters, as_dict=1)

	return register

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`employee`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 

def get_data(filters):
	tr_map = get_transaction_map()
	schedule = frappe.db.get_value("Payroll Period", filters.period, "schedule")
	employees = frappe.db.sql("""SELECT `name`, full_name FROM `tabEmployee` 
		WHERE company = %(company)s AND payroll_schedule = %(schedule)s """, {
			"schedule": schedule,
			"company": filters.company,
		}, as_dict=1)

	emp_map = frappe._dict()
	for emp in employees:
		emp_map.setdefault(emp.name, frappe._dict({
				"full_name": emp.full_name,
				"registers": [],
			})
		)

	registers = get_register(filters)
	emp_map = get_employee_wise_register(emp_map, registers)
	data = []
	for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['full_name']):
		sub_total = 0.0
		if emp_dict['registers']:
			data.append({
				"deduction_type":"<b>"+cstr(emp_dict.get('full_name'))+"</b>",
			})

			for r in emp_dict['registers']:
				sub_total += r.amount
				data.append({
						"deduction_type": tr_map[r.pay_code]['title'],
						"code": r.pay_code,
						"amount": r.amount,
					})

			data.append({
				"deduction_type": "<b> Total </b>",
				"amount": sub_total,
			})

			data.append({})

	return data

def get_employee_wise_register(emp_map, registers):
	for r in registers:
		if r.employee in emp_map:
			emp_map[r.employee].registers.append(r)

	return emp_map

def get_result_as_list(data, filters):
	result = []
	for d in data:		
		result.append(d)
	return result