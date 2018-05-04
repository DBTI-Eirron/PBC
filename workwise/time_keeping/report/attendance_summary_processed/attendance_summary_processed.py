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
	pay_from, pay_to = frappe.db.get_value("Payroll Period", filters.payroll_period, ["from_date", "to_date"])
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
				tags += " <span class='label label-danger'> Late </span> " if r['late'] > 0 else ""
				tags += " <span class='label label-success'> Overtime </span> " if 	r['overtime'] > 0 else ""
				tags += " <span class='label label-danger'> Undertime </span> " if 	r['undertime'] > 0 else ""
				if 	r['is_leave'] == 1:
					tags += " <span class='label label-success'>"+ cstr(r['leave_name']) +" </span> "


				if 	r['is_halfday'] == 1:
					tags += " <span class='label label-info'> Halfday </span> "

				tags += " <span class='label label-success'> Official Business </span> " if r['is_ob'] else ""
				
				if 	r['is_absent'] == 1:
					tags += " <span class='label label-danger'> Absent </span> "

				if 	r['is_lwop'] == 1:
					tags += " <span class='label label-danger'> LWOP </span> "
				
				if 	r['is_flexible'] == 1:
					tags += " <span class='label label-info'> Flexible </span> "

				if 	r['is_restday'] == 1:
					tags += " <span class='label label-info'> Rest Day </span> "		
				
				if 	r['is_holiday'] == 1:
					tags += " <span class='label label-info'> Holiday </span> "

				if 	r['is_sp_holiday'] == 1:
					tags += " <span class='label label-info'> Special Holiday </span> "

				if 	r['has_issue'] == 1:
					tags += " <span class='label label-warning'> ! Attendance Has Issue ! </span> "

				r["tags"] = tags
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