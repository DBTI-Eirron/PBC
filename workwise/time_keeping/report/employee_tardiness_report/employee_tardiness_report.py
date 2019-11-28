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
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "late",
			"label": _("Late"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "undertime",
			"label": _("Undertime"),
			"fieldtype": "Data",
			"width": 100
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
	register = frappe.db.sql("""SELECT DISTINCT * FROM `tabAttendance Register` 
		WHERE employee = %(employee)s AND target_date >= %(from_date)s AND target_date <= %(to_date)s
		AND work > 0
		AND (late > 0 OR undertime > 0)
		ORDER BY target_date ASC""",{
			"employee": emp,
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)

	return register

def get_data(filters):
	#Initialize
	data = []
	pay_from, pay_to = filters.from_date, filters.to_date
	employees = get_employees(filters)

	data.append({"target_date":"<b>Company: </b>"+filters.company+"",})
	if filters.department:
		data.append({"target_date":"<b>Department: </b>"+filters.department+"</b>",})
	data.append({"target_date":"<b>Period: </b>"+cstr(filters.from_date)+" - "+cstr(filters.to_date)+"</b>",})
	data.append({})

	for emp in employees:
		register = get_register(emp.name, pay_from, pay_to)
		if register:
			total_work = 0.00
			total_late = 0.00
			total_ut = 0.00
			data.append({"target_date":"<b>"+emp.full_name+"</b>",})
			for r in register:
				#if r.late > 0 or r.undertime > 0:
				
				total_late += r.late
				total_work += r.work
				total_ut += r.undertime

				data.append({
					"target_date": r.target_date,
					"work_shift": r.work_shift,
					"card_in": r.card_in,
					"card_out": r.card_out,
					"work": '{:,.2f}'.format(convert_hrs(filters ,r.work)),
					"late": '{:,.2f}'.format(convert_hrs(filters ,r.late)),
					"undertime": '{:,.2f}'.format(convert_hrs(filters ,r.undertime)),
				})

			data.append({
				"target_date": _("TOTAL"),
				"work_shift": "",
				"card_in": "",
				"card_out": "",
				"work": '{:,.2f}'.format(convert_hrs(filters ,total_work)),
				"late": '{:,.2f}'.format(convert_hrs(filters ,total_late)),
				"undertime": '{:,.2f}'.format(convert_hrs(filters ,total_ut)),
			})
			data.append({})

	return data

def get_employees(filters):
	register = frappe.db.sql("""SELECT DISTINCT TE.`name`, TE.full_name FROM `tabEmployee` TE
		LEFT JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name`
		WHERE TE.is_active = 1 AND TE.employment_status != 'Retired' AND TE.company = %(company)s {conditions} ORDER BY TE.`full_name` """.format(conditions=get_conditions(filters)), filters, as_dict=1)

	return register

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("TE.`name`=%(employee)s")

	if filters.get("department"):
		lft, rgt = frappe.db.get_value("Department", filters.department, ["lft", "rgt"])
		conditions.append(_("( DEPT.`lft` BETWEEN '{0}' AND '{1}' )").format(lft, rgt))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

def get_result_as_list(data, filters):
	result = []
	for d in data:		
		result.append(d)
	return result

def convert_hrs(filters, hrs):
	con = 0
	if filters.time_options == "Mins":
		con = flt(hrs, 8) * 60
	else:
		con = flt(hrs, 8)

	return flt(con, 8)