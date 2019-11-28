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
			"fieldtype": "Data",
			"width": 60
		},
		{
			"fieldname": "break",
			"label": _("Break"),
			"fieldtype": "Data",
			"width": 60
		},		
		{
			"fieldname": "late",
			"label": _("Late"),
			"fieldtype": "Data",
			"width": 60
		},
		{
			"fieldname": "overtime",
			"label": _("OT"),
			"fieldtype": "Data",
			"width": 60
		},
		{
			"fieldname": "overtime_nd",
			"label": _("OT ND"),
			"fieldtype": "Data",
			"width": 60
		},
		{
			"fieldname": "overtime_ex",
			"label": _("OT EX"),
			"fieldtype": "Data",
			"width": 60
		},
		{
			"fieldname": "nightdiff",
			"label": _("ND"),
			"fieldtype": "Data",
			"width": 60
		},
		{
			"fieldname": "cto",
			"label": _("CTO"),
			"fieldtype": "Data",
			"width": 60
		},
		{
			"fieldname": "undertime",
			"label": _("UT"),
			"fieldtype": "Data",
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

	if filters.flt_precision:
		precision_fields = ["work","break","late","overtime","overtime_ex","overtime_nd","nightdiff","cto","undertime"]
		for d in columns:
			if d.get('fieldname') in precision_fields:
				d['precision'] = cint(filters.flt_precision)

	return columns

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_data(filters):
	#Initialize
	data = []
	department_included = [filters.department]

	pay_from, pay_to, schedule = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to", "schedule"])
	emp_map = init_employee_map(filters, pay_from, pay_to, schedule)
	grand_work, grand_break, grand_late, grand_ot, grand_otnd, grand_otex, grand_ut, grand_nd = 0, 0, 0, 0, 0, 0, 0, 0

	for emp, emp_dict in sorted(emp_map.items(), key=lambda x: (x[1]['employee_name'], x[1]['lft']) ):
		if emp_dict['registers']:
			if (filters.department) and (emp_dict['department'] not in department_included):
				data.append({
					"target_date":"<b>Department: </b>"+emp_dict['department']+"</b>",
				})
				department_included.append(emp_dict['department'])

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
	emp_map = frappe._dict()
	emp = frappe.db.sql(""" SELECT name, `user_id` FROM `tabEmployee` WHERE user_id = %s AND user_id != "" AND user_id is not null LIMIT 1""",( frappe.session.user ), as_dict=1)
	if emp:
		employees = frappe.db.sql("""SELECT TE.`name`, TE.full_name, TE.company, TE.`department`, DEPT.`lft` FROM `tabEmployee` TE
			LEFT JOIN `tabDepartment` DEPT ON TE.`department` = DEPT.`name`
			WHERE TE.name = %(employee)s """,{ "employee": emp[0].name }, as_dict=1)

		for emp in employees:
			emp_map.setdefault(emp.name, frappe._dict({
					"employee": emp.name,
					"employee_name": emp.full_name,
					"company": emp.company,
					"department": emp.department,
					"lft": emp.lft,
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

def get_result_as_list(data, filters):
	result = []
	for d in data:		
		result.append(d)

	return result