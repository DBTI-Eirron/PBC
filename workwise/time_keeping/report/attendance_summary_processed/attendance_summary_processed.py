# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

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
			"fieldname": "overtime_nd",
			"label": _("OT ND"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "overtime_ex",
			"label": _("OT EX"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "nightdiff",
			"label": _("ND"),
			"fieldtype": "Float",
			"width": 60
		},
		{
			"fieldname": "cto",
			"label": _("CTO"),
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
		{
			"fieldname": "links",
			"label": _("Links"),
			"fieldtype": "Data",
			"width": 400
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
	pay_from, pay_to, schedule = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to", "schedule"])
	emp_map = init_employee_map(filters, pay_from, pay_to, schedule)
	grand_work, grand_break, grand_late, grand_ot, grand_otnd, grand_otex, grand_ut, grand_nd = 0, 0, 0, 0, 0, 0, 0, 0
	data.append({
		"target_date":"<b>Company: </b>"+filters.company+"",
	})
	if filters.department:
		data.append({
			"target_date":"<b>Department: </b>"+filters.department+"</b>",
		})
	if filters.location:
		data.append({
			"target_date":"<b>Location: </b>"+filters.location+"</b>",
		})
	data.append({
		"target_date":"<b>Period: </b>"+cstr(filters.payroll_period)+"</b>",
	})

	data.append({})
	for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
		data.append({"target_date":"<b>"+emp_dict['employee_name']+"</b>"}) #add employee name header
		for r in emp_dict['registers']:
			emp_dict['sub_work'] += r.work
			emp_dict['sub_break'] += r.get('break')
			emp_dict['sub_late'] += r.late
			emp_dict['sub_overtime'] += r.overtime
			emp_dict['sub_overtime_nd'] += r.overtime_nd
			emp_dict['sub_overtime_ex'] += r.overtime_ex
			emp_dict['sub_nightdiff'] += r.nightdiff
			emp_dict['sub_undertime'] += r.undertime
			data.append(r)

		grand_work += emp_dict['sub_work']
		grand_break += emp_dict['sub_break']
		grand_late += emp_dict['sub_late']
		grand_ot += emp_dict['sub_overtime']
		grand_otnd += emp_dict['sub_overtime_nd']
		grand_otex += emp_dict['sub_overtime_ex']
		grand_nd += emp_dict['sub_nightdiff']
		grand_ut += emp_dict['sub_undertime']
		data.append({
			"target_date": _("TOTAL"),
			"work": emp_dict['sub_work'],
			"break": emp_dict['sub_break'],
			"late": emp_dict['sub_late'],
			"overtime": emp_dict['sub_overtime'],
			"overtime_nd": emp_dict['sub_overtime_nd'],
			"overtime_ex": emp_dict['sub_overtime_ex'],
			"nightdiff": emp_dict['sub_nightdiff'],
			"undertime": emp_dict['sub_undertime'],
		})
		data.append({})

	data.append({
		"target_date": _("GRAND TOTAL"),
		"work": grand_work,
		"break": grand_break,
		"late": grand_late,
		"overtime": grand_ot,
		"overtime_nd": grand_otnd,
		"overtime_ex": grand_otex,
		"nightdiff": grand_nd,
		"undertime": grand_ut,
	})

	return data

def init_employee_map(filters, pay_from, pay_to, schedule):
	employees = frappe.db.sql("""SELECT `name`, full_name, company FROM `tabEmployee` 
		WHERE is_active = 1 AND company = %(company)s {conditions} ORDER BY full_name""".format(conditions=get_conditions(filters, schedule)), filters, as_dict=1)

	emp_map = frappe._dict()
	for emp in employees:
		emp_map.setdefault(emp.name, frappe._dict({
				"employee": emp.name,
				"employee_name": emp.full_name,
				"company": emp.company,
				"registers": [],
				"target_date": "",
				"sub_work": 0.0,
				"sub_break": 0.0,
				"sub_late": 0.0,
				"sub_overtime": 0.0,
				"sub_overtime_nd": 0.0,
				"sub_overtime_ex": 0.0,
				"sub_nightdiff": 0.0,
				"sub_undertime": 0.0,
			})
		)

	get_employee_wise_registers(emp_map, pay_from, pay_to)

	return emp_map

def get_employee_wise_registers(emp_map, pay_from, pay_to):
	register = frappe.db.sql("""SELECT * FROM `tabAttendance Register` 
		WHERE target_date >= %(from_date)s AND target_date <= %(to_date)s
		ORDER BY target_date ASC""",{
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)

	for rg in register:
		if rg.employee in emp_map:
			emp_map[rg.employee].registers.append(rg)

def get_conditions(filters, schedule):
	conditions = []
	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")

	if filters.get("department"):
		conditions.append("department=%(department)s")

	if filters.get("location"):
		conditions.append("location=%(location)s")

	if filters.get("position_title"):
		conditions.append("position_title=%(position_title)s")

	if not filters.ignore_payroll_schedule:
		conditions.append(_("payroll_schedule='"+_(cstr(schedule))+"'"))

	return "and {}".format(" and ".join(conditions)) if conditions else "" 

def get_result_as_list(data, filters):
	result = []
	for d in data:		
		result.append(d)

	return result