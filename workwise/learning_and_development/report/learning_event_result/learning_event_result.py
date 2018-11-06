# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	employee_list = get_employees(filters)
	
	if not employee_list:
		frappe.throw(_("No record found"))
		return columns, employee_list

	data = []
	tna = ""
	tnas = frappe.db.sql("""SELECT DISTINCT `name`, learning_program FROM `tabLearning Event` WHERE `event_status` != "Cancelled" and `name` = %s """, (filters.training_name), as_dict=True)
	for t in tnas:
		tna = t.learning_program

	objectives = frappe.db.sql("""SELECT DISTINCT `objective` FROM `tabLearning Objective Table` WHERE `parenttype` = "Learning Program" and `parent` = %s """, (tna), as_dict=True)

	for emp in employee_list:
		grd = ""
		row = [emp.employee, emp.employee_name]

		for obj in objectives:
			eval_score = frappe.db.sql("""SELECT DISTINCT ET.grade FROM `tabLearning Evaluation` LE JOIN `tabLearning Evaluation Table` ET ON LE.`name` = ET.`parent` WHERE LE.event_type = "Learning Event" AND LE.docstatus = 1 AND LE.event = %s AND LE.employee = %s AND ET.objective = %s """, (filters.training_name, emp.employee, obj.objective), as_dict=True)
			for d in eval_score:
				if d.grade:
					grd = d.grade
				else:
					grd = 0
			row.append(grd)

		row.append(emp.final_grade)
		row.append(emp.comment)
		data.append(row)

	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 200
		},
	]

	tna = frappe.db.sql("""SELECT DISTINCT * FROM `tabLearning Event` WHERE `event_status` != "Cancelled" and `name` = %s """, (filters.training_name), as_dict=True)
	for t in tna:
		objectives = frappe.db.sql("""SELECT DISTINCT * FROM `tabLearning Objective Table` WHERE `parenttype` = "Learning Program" and `parent` = %s """, (t.learning_program), as_dict=True)
		if objectives:
			for d in objectives:
				columns += [
					{
						"fieldname": d.objective,
						"label": _(d.objective),
						"fieldtype": "Data",
						"width": 160
					},
				]

	columns += [	
		{
			"fieldname": "final_grade",
			"label": _("Final Grade"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "comment",
			"label": _("Comment"),
			"fieldtype": "Data",
			"width": 200
		},
	]

	return columns

def get_employees(filters):
	employees = frappe.db.sql("""SELECT DISTINCT `employee`, employee_name, final_grade, comment FROM `tabLearning Evaluation`
		WHERE event_type = "Learning Event" AND docstatus = 1 AND event = %s AND company = %s """, (filters.training_name, filters.company), as_dict=True)

	return employees

def get_conditions(filters):
	conditions = []
	if filters.get("training_name"):
		conditions.append("`event`=%(training_name)s")

	if filters.get("employee"):
		conditions.append("`employee`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 