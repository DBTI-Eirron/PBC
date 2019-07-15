# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

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
			"fieldname": "target_date",
			"label": _("Data"),
			"fieldtype": "Data",
			"width": 300
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
			"fieldname": "late",
			"label": _("Late"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "undertime",
			"label": _("Undertime"),
			"fieldtype": "Float",
			"width": 80
		},
	]

	return columns

def get_result(filters):

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be less than To Date"))
	else:
		data = get_data(filters)
		result = get_result_as_list(data, filters)

	return result

def get_register(emp, pay_from, pay_to):
	register = frappe.db.sql("""SELECT * FROM `tabAttendance Register` 
		WHERE employee = %(employee)s AND (`target_date` BETWEEN %(from_date)s AND %(to_date)s)
		AND is_restday != 1 
		AND is_leave != 1
		AND is_holiday != 1
		AND is_ob != 1
		ORDER BY target_date ASC""",{
			"employee": emp,
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)

	return register

def get_data(filters):
	#Initialize

	filters_company = ""
	filters_employee = ""
	employees = frappe.db.sql("""SELECT `name`, company FROM `tabEmployee` WHERE `user_id` = %s LIMIT 1""",( frappe.session.user ), as_dict=1)
	for d in employees:
		filters_company = d.company
		filters_employee = d.name

	data = []
	pay_from, pay_to = filters.from_date, filters.to_date
	employees = get_employees(filters, filters_company, filters_employee)
	data.append({
		"target_date":"<b>Company: </b>"+filters_company+"",
	})

	data.append({
		"target_date":"<b>Period: </b>"+cstr(filters.from_date)+" - "+cstr(filters.to_date)+"</b>",
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
				total_work += r.work
				total_break += r['break']
				total_late += r.late
				total_ot += r.overtime
				total_ut += r.undertime
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

def get_employees(filters, filters_company, filters_employee):

	register = frappe.db.sql("""SELECT `name`, full_name FROM `tabEmployee` 
		WHERE is_active = 1 AND employment_status != 'Retired' AND company = %(company)s AND `name` = %(employee)s""",{
			"company": filters_company,
			"employee": filters_employee,
		}, as_dict=True)

	return register

def get_result_as_list(data, filters):
	result = []
	for d in data:		
		result.append(d)
	return result