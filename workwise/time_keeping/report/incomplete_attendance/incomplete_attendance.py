# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "emp_name",
			"label": _("Data"),
			"fieldtype": "Data",
			"width": 350
		},
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "shift",
			"label": _("Shift"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "time_in",
			"label": _("Time In"),
			"fieldtype": "Data",
			"width": 130
		},		
		{
			"fieldname": "time_out",
			"label": _("Time Out"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "particulars",
			"label": _("Particulars"),
			"fieldtype": "Data",
			"width": 200
		},
	]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_register(emp, pay_from, pay_to):
	register = frappe.db.sql("""SELECT * FROM `tabAttendance Register` 
		WHERE employee = %(employee)s AND target_date >= %(from_date)s AND target_date <= %(to_date)s AND (late > 0 OR undertime > 0 OR is_absent = 1)
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
		"emp_name":"<b>Company: </b>"+filters.company+"",
	})
	if filters.department:
		data.append({
			"emp_name":"<b>Department: </b>"+filters.department+"</b>",
		})
	data.append({
		"emp_name":"<b>Period: </b>"+cstr(filters.payroll_period)+"</b>",
	})

	data.append({})

	for emp in employees:
		register = get_register(emp.name, pay_from, pay_to)
		if register:
			data.append({
				"emp_name":"<b>Employee Name: </b>"+cstr(emp.full_name)+"</b>",
			})
			data.append({
				"emp_name":"<b>ID Number: </b>"+cstr(emp.name)+"</b>",
			})
			
			for r in register:
				emp_late = 0
				schedule = ""
				schedule = frappe.db.sql("""SELECT employee, company, work_shift, work_hours, break_mins, target_date, shift_type, 
					datetime_in, datetime_out, pre_shift, post_shift, break_start, break_end, nd_start, nd_end
					FROM `tabWork Schedule` 
					WHERE employee = %(employee)s AND target_date = %(date)s
					ORDER BY target_date ASC""",{
						"employee": r.employee,
						"date": r.target_date,
				}, as_dict=True)
				for s in schedule:
					shift = ""
					shift = frappe.db.sql("""SELECT `name`, grace_period, b_grace_period, is_restday, is_flexible, setup_preshift, setup_postshift, ignore_late
						FROM `tabWork Shift` WHERE `name` = %(w_shift)s """,{
						"w_shift": r.work_shift,
					}, as_dict=True)
					for w in shift:
						if r.is_leave != 0 and r.is_holiday != 0 and r.is_ob != 0 and r.is_lwop != 0:
							if r.card_in > s.time_in + datetime.timedelta(minutes=w.grace):
								if frappe.db.get_single_value('Timekeeping Settings', 'graceperiod_late'):
									emp_late += ( r.card_in - (s.time_in + datetime.timedelta(minutes=w.grace))  ).total_seconds()
								else:
									emp_late += (r.card_in - s.time_in).total_seconds()
						if r.late > 0:
							emp_late = 1

				tags = ""
				if (emp_late > 0) or (r.undertime > 0) or (r.is_absent == 1):
					tags += " <span class='label label-danger'> Late </span> " if emp_late > 0 else ""
					tags += " <span class='label label-danger'> Undertime </span> " if 	r['undertime'] > 0 else ""
					if 	r.is_absent == 1:
						tags += " <span class='label label-danger'> Absent </span> "

					if tags and tags != "":
						data.append({
							"date": r.target_date,
							"shift": r.work_shift,
							"time_in": r.card_in,
							"time_out": r.card_out,
							"particulars": tags,
						})	

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