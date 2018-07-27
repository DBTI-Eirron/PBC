# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "effectivity_date",
			"label": _("Effectivity Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "employee_id",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 140
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 200
		},
	]

	if filters.movement_type == "Job Rotation":
		columns += [
			{
				"fieldname": "job_rotation_type",
				"label": _("Job Rotation Type"),
				"fieldtype": "Select",
				"fieldtype": "Data",
				"width": 200
			},
			{
				"fieldname": "current_position",
				"label": _("From Position"),
				"fieldtype": "Data",
				"width": 200
			},
			{
				"fieldname": "new_position",
				"label": _("To Position"),
				"fieldtype": "Data",
				"width": 200
			},
		]

	if filters.movement_type == "Retirement":
		columns += [
			{
				"fieldname": "retirement_type",
				"label": _("Retirement Type"),
				"fieldtype": "Data",
				"width": 200
			},
		]

	if filters.movement_type == "Resignation":
		columns += [
			{
				"fieldname": "resignation_type",
				"label": _("Resignation Type"),
				"fieldtype": "Data",
				"width": 200
			},
		]

	if filters.movement_type == "Transfer":
		columns += [
			{
				"fieldname": "transfer_type",
				"label": _("Transfer Type"),
				"fieldtype": "Data",
				"width": 200
			},
			{
				"fieldname": "current_department",
				"label": _("From Department"),
				"fieldtype": "Data",
				"width": 200
			},
			{
				"fieldname": "current_location",
				"label": _("From Location"),
				"fieldtype": "Data",
				"width": 200
			},
			{
				"fieldname": "new_department",
				"label": _("To Department"),
				"fieldtype": "Data",
				"width": 200
			},
			{
				"fieldname": "new_location",
				"label": _("To Location"),
				"fieldtype": "Data",
				"width": 200
			},
		]

	if filters.movement_type == "Termination":
		columns += [
			{
				"fieldname": "termination_due_to",
				"label": _("Termination Due To"),
				"fieldtype": "Data",
				"width": 200
			},
		]

	if filters.movement_type == "Salary Adjustment":
		columns += [
			{
				"fieldname": "salary_adjustment_type",
				"label": _("Salary Adjustment Type"),
				"fieldtype": "Data",
				"width": 200
			},
		]

	if filters.movement_type == "Extension of Services":
		columns += [
			{
				"fieldname": "current_end_of_contract",
				"label": _("End of Contract"),
				"fieldtype": "Data",
				"width": 200
			},
			{
				"fieldname": "new_end_of_contract",
				"label": _("New End of Contract"),
				"fieldtype": "Data",
				"width": 200
			},
			{
				"fieldname": "s_remarks",
				"label": _("Remarks"),
				"fieldtype": "Data",
				"width": 300
			},
		]

	if filters.movement_type != "Extension of Services":
		columns += [
				{
					"fieldname": "remarks",
					"label": _("Remarks"),
					"fieldtype": "Data",
					"width": 300
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

	employees = get_employees(filters)
	for emp in employees:
		movements = frappe.db.sql(""" SELECT * FROM `tabEmployee Movement` WHERE `docstatus` = 1 AND `effective_on` >= %s AND `effective_on` <= %s AND `movement_type` = %s AND `employee` = %s """, (filters.from_date, filters.to_date, filters.movement_type, emp.name),as_dict=True)
		for movement in movements:
			entry = {
				"effectivity_date": movement.effective_on,
				"employee_id": movement.employee,
				"employee_name": movement.employee_name,
				"job_rotation_type": movement.job_rotation_type,
				"current_position": movement.current_position,
				"new_position": movement.new_position,
				"remarks": movement.remarks,
				"retirement_type": movement.retirement_type,
				"resignation_type": movement.resignation_type,
				"transfer_type": movement.transfer_type,
				"current_department": movement.current_department,
				"current_location": movement.current_location,
				"new_department": movement.new_department,
				"new_location": movement.new_location,
				"termination_due_to": movement.termination_due_to,
				"salary_adjustment_type": movement.salary_adjustment_type,
				"current_end_of_contract": movement.current_end_of_contract,
				"new_end_of_contract": movement.new_end_of_contract,
				"s_remarks": movement.s_remarks,
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