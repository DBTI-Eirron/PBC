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
	tnas = frappe.db.sql("""SELECT DISTINCT `name` FROM `tabTraining Needs Analysis` WHERE `status` != "Cancelled" and `name` = %s """, (filters.training_name), as_dict=True)
	for t in tnas:
		tna = t.name

	objectives = frappe.db.sql("""SELECT objective FROM `tabLearning Objective Table` WHERE `parenttype` = "Training Needs Analysis" and `parent` = %s """, (tna), as_dict=True)

	for emp in employee_list:
		row = [emp.employee, emp.employee_name]

		for obj in objectives:
			eval_score = frappe.db.sql("""SELECT DISTINCT ET.grade FROM `tabLearning Evaluation` LE JOIN `tabLearning Evaluation Table` ET ON LE.`name` = ET.`parent` WHERE LE.event_type = "Training Needs Analysis" AND LE.event = %s AND LE.employee = %s AND ET.objective = %s """, (filters.training_name, emp.employee, obj.objective), as_dict=True)
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

	tna = frappe.db.sql("""SELECT DISTINCT `name` FROM `tabTraining Needs Analysis` WHERE `status` != "Cancelled" and `name` = %s """, (filters.training_name), as_dict=True)
	for t in tna:
		objectives = frappe.db.sql("""SELECT * FROM `tabLearning Objective Table` WHERE `parenttype` = "Training Needs Analysis" and `parent` = %s """, (t.name), as_dict=True)
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
			"width": 300
		},
	]

	return columns

def get_employees(filters):
	employees = frappe.db.sql("""SELECT `employee`, employee_name, final_grade, comment	FROM `tabLearning Evaluation`
		WHERE event_type = "Training Needs Analysis" AND docstatus = 1 AND event = %s AND company = %s """, (filters.training_name, filters.company), as_dict=True)

	return employees

def get_conditions(filters):
	conditions = []
	if filters.get("training_name"):
		conditions.append("`event`=%(training_name)s")

	if filters.get("employee"):
		conditions.append("`employee`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 

def get_evaluation_map(tna, emp, obj):
	eval_score = frappe.db.sql("""SELECT DISTINCT ET.grade FROM `tabLearning Evaluation Table` ET INNER JOIN `tabLearning Evaluation` LE ON ET.`parent` = LE.`name` WHERE ET.parent = %s AND LE.employee = %s AND ET.objective = %s LIMIT 1""", (tna, emp.employee, obj.objective), as_dict=True)
	if not eval_score:
		eval_score = 0

	return eval_score