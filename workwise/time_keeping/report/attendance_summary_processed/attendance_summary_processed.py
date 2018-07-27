# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
value_fields = ("opening_debit", "opening_credit", "debit", "credit", "closing_debit", "closing_credit")

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "target_date",
			"label": _("Data"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "work_shift",
			"label": _("Shift"),
			"fieldtype": "Link",
			"options": "Work Shift",
			"width": 130
		},
		{
			"fieldname": "card_in",
			"label": _("Time IN"),
			"fieldtype": "Date",
			"width": 130
		},
	]


	if filters.show_break:
		columns += [
			{
				"fieldname": "break_out",
				"label": _("Break OUT"),
				"fieldtype": "Data",
				"width": 140
			},
			{
				"fieldname": "break_in",
				"label": _("Break IN"),
				"fieldtype": "Data",
				"width": 140
			},
		]

	columns += [
		{
			"fieldname": "card_out",
			"label": _("Time OUT"),
			"fieldtype": "Date",
			"width": 130
		},
		{
			"fieldname": "work",
			"label": _("Work"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "break",
			"label": _("Break"),
			"fieldtype": "Float",
			"width": 60
		},		
		{
			"fieldname": "late",
			"label": _("Late"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "overtime",
			"label": _("OT"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "undertime",
			"label": _("UT"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "tags",
			"label": _("Tags"),
			"fieldtype": "Data",
			"width": 400
		},
	]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_register(emp, pay_from, pay_to):
	register = frappe.db.sql("""SELECT * FROM `tabAttendance Register` 
		WHERE employee = %(employee)s AND target_date >= %(from_date)s AND target_date <= %(to_date)s
		ORDER BY target_date ASC""",{
			"employee": emp,
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)

	return register

def get_data(filters):
	#Initialize
	data = []
	pay_from, pay_to = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to"])
	employees = get_employees(filters)
	data.append({
		"target_date":"<b>Company: </b>"+filters.company+"",
	})
	if filters.department:
		data.append({
			"target_date":"<b>Department: </b>"+filters.department+"</b>",
		})
	data.append({
		"target_date":"<b>Period: </b>"+cstr(filters.payroll_period)+"</b>",
	})

	data.append({})

	for emp in employees:
		register = get_register(emp.name, pay_from, pay_to)
		if register:
			total_work = 0
			total_break = 0
			total_late = 0
			total_ot = 0
			total_ut = 0
			data.append({
					"target_date":"<b>"+emp.full_name+"</b>",
				})
			for r in register: 
				tags = ""
				total_work += r['work']
				total_break += r['break']
				total_late += r['late']
				total_ot += r['overtime']
				total_ut += r['undertime']
				data.append(r)

			data.append({
					"target_date": _("TOTAL"),
					"work": total_work,
					"break": total_break,
					"late": total_late,
					"overtime": total_ot,
					"undertime": total_ut,
				})

			data.append({})


	return data

def get_employees(filters):
	register = frappe.db.sql("""SELECT `name`, full_name FROM `tabEmployee` 
		WHERE company = %(company)s {conditions}""".format(conditions=get_conditions(filters)), filters, as_dict=1)

	return register

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")

	if filters.get("department"):
		conditions.append("department=%(department)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 

def get_result_as_list(data, filters):
	result = []
	for d in data:		
		result.append(d)
	return result