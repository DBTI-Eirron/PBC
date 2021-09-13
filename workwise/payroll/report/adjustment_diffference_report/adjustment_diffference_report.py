# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _, msgprint

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	#data, columns = get_data(filters, columns)
	data = formatted_report(filters, columns)

	return columns, data

def get_columns():
	#Standard
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 160
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 260
		},
		{
			"fieldname": "processed_work_hrs",
			"label": _("Processed Work Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "processed_absent_hrs",
			"label": _("Processed Absent Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "processed_undertime_hrs",
			"label": _("Processed Undertime Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "processed_nd_hrs",
			"label": _("Processed Night Differential Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "processed_late_hrs",
			"label": _("Processed Late Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "processed_overtime_hrs",
			"label": _("Processed Overtime Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "processed_cto_hrs",
			"label": _("Processed Compensatory Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "adjusted_work_hrs",
			"label": _("Adjusted Work Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "adjusted_absent_hrs",
			"label": _("Adjusted Absent Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "adjusted_undertime_hrs",
			"label": _("Adjusted Undertime Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "adjusted_nd_hrs",
			"label": _("Adjusted Night Differential Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "adjusted_late_hrs",
			"label": _("Adjusted Late Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "adjusted_overtime_hrs",
			"label": _("Adjusted Overtime Hours"),
			"fieldtype": "Float",
			"width": 160
		},
		{
			"fieldname": "adjusted_cto_hrs",
			"label": _("Adjusted Compensatory Hours"),
			"fieldtype": "Float",
			"width": 160
		}
	]

	#Custom
	columns = [
		{
			"fieldname": "row_1",
			"label": _(""),
			"fieldtype": "Data",
			"width": 300
		},
		{
			"fieldname": "row_2",
			"label": _(""),
			"fieldtype": "Data",
			"width": 90
		},
		{
			"fieldname": "row_3",
			"label": _(""),
			"fieldtype": "Data",
			"width": 90
		},
		{
			"fieldname": "row_4",
			"label": _(""),
			"fieldtype": "Data",
			"width": 300
		},
		{
			"fieldname": "row_5",
			"label": _(""),
			"fieldtype": "Data",
			"width": 300
		},
	]

	return columns

def get_data(filters, columns):
	data = []
	totals = {}
	fields = ["processed_work_hrs", "processed_absent_hrs", "processed_undertime_hrs", "processed_nd_hrs", 
		"processed_late_hrs", "processed_overtime_hrs", "processed_cto_hrs", "adjusted_work_hrs", "adjusted_absent_hrs", 
		"adjusted_undertime_hrs", "adjusted_nd_hrs", "adjusted_late_hrs", "adjusted_overtime_hrs", "adjusted_cto_hrs"]

	register = get_registers(filters)

	for reg in register:
		row_data = {
			"employee": reg.employee,
			"employee_name": reg.employee_name,
		}
		for fl in fields:
			if fl not in totals:
				totals[fl] = 0

			row_data[fl] = 0
			if fl in reg:
				row_data[fl] = reg[fl]
				totals[fl] += reg[fl]
		data.append(row_data)

	if filters.hide_zero:
		for tot in totals:
			if totals[tot] <= 0:
				for cl in columns:
					if cl['fieldname'] == tot:
						cl['hidden'] = 1

	return data, columns

def get_registers(filters):
	register = frappe.db.sql("""SELECT * FROM `tabAdjustment Register` 
		WHERE `company` = %(company)s AND `payroll_period` = %(period)s AND `target_period` = %(target_period)s {conditions}
		ORDER BY `employee_name` ASC""".format(conditions=get_conditions(filters)),{
		"company": filters.company,
		"period": filters.period,
		"target_period": filters.target_period,
		"employee": filters.employee,
	}, as_dict=True)

	return register

def get_conditions(filters):
	conditions = []
	if filters.employee:
		conditions.append("`employee` = %(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 


def formatted_report(filters, columns):
	data = []
	rows = {'row_1', 'row_2', 'row_3', 'row_4', 'row_5'}
	attendance_type = ['Work Hours', 'Overtime', 'Undertime', 'Late', 'Night Differential', 'Absent', 'Unpaid Holiday', 'Compensatory']
	column_labels = ['Attendance Type', 'Processed', 'Adjusted', 'Processed Application', 'Adjusted Application']
	register = get_registers(filters)

	if register:
		#Header
		data.append({'row_1': filters.company})
		data.append({'row_1': str(filters.period)+' - '+str(filters.target_period)})
		data.append({})

		#Data
		for reg in register:
			#Data Header
			data.append({'row_1': reg.employee_name})
			data.append({
				'row_1': 'Attendance Type',
				'row_2': 'Processed',
				'row_3': 'Adjusted',
				'row_4': 'Processed Application',
				'row_5': 'Adjusted Application',
			})
			row = {}
			for at in attendance_type:
				row['row_1'] = str(at)
				row['row_4'] = ""
				row['row_5'] = ""
				if at == 'Work Hours':
					row['row_2'] = reg.processed_work_hrs
					row['row_3'] = reg.adjusted_work_hrs
				if at == 'Overtime':
					row['row_2'] = reg.processed_overtime_hrs
					row['row_3'] = reg.adjusted_overtime_hrs
					if reg.processed_overtime_application_links:
						for d in eval(reg.processed_overtime_application_links):
							row['row_4'] += "<span class='label label-info'><a href='/desk#Form/Overtime Application/"+d+"'> "+d+" </a></span>"
					if reg.adjusted_overtime_application_links:
						for d in eval(reg.adjusted_overtime_application_links):
							row['row_5'] += "<span class='label label-info'><a href='/desk#Form/Overtime Application/"+d+"'> "+d+" </a></span>"
						
				if at == 'Undertime':
					row['row_2'] = reg.processed_undertime_hrs
					row['row_3'] = reg.adjusted_undertime_hrs
					if reg.processed_undertime_application_links:
						for d in eval(reg.processed_undertime_application_links):
							row['row_4'] += "<span class='label label-info'><a href='/desk#Form/Undertime Application/"+d+"'> "+d+" </a></span>"
					if reg.adjusted_undertime_application_links:
						for d in eval(reg.adjusted_undertime_application_links):
							row['row_5'] += "<span class='label label-info'><a href='/desk#Form/Undertime Application/"+d+"'> "+d+" </a></span>"

				if at == 'Late':
					row['row_2'] = reg.processed_late_hrs
					row['row_3'] = reg.adjusted_late_hrs
				if at == 'Night Differential':
					row['row_2'] = reg.processed_nd_hrs
					row['row_3'] = reg.adjusted_nd_hrs
				if at == 'Absent':
					row['row_2'] = reg.processed_absent_hrs
					row['row_3'] = reg.adjusted_absent_hrs
					if reg.processed_leave_application_links:
						for d in eval(reg.processed_leave_application_links):
							row['row_4'] += "<span class='label label-info'><a href='/desk#Form/Leave Application/"+d+"'> "+d+" </a></span>"
					if reg.adjusted_leave_application_links:
						for d in eval(reg.adjusted_leave_application_links):
							row['row_5'] += "<span class='label label-info'><a href='/desk#Form/Leave Application/"+d+"'> "+d+" </a></span>"

				if at == 'Unpaid Holiday':
					row['row_2'] = reg.processed_uho_hrs
					row['row_3'] = reg.adjusted_uho_hrs
				if at == 'Compensatory':
					row['row_2'] = reg.processed_cto_hrs
					row['row_3'] = reg.adjusted_cto_hrs
					if reg.processed_compensatory_time_off_links:
						for d in eval(reg.processed_compensatory_time_off_links):
							row['row_4'] += "<span class='label label-info'><a href='/desk#Form/Compensatory Time Off/"+d+"'> "+d+" </a></span>"
					if reg.adjusted_compensatory_time_off_links:
						for d in eval(reg.adjusted_compensatory_time_off_links):
							row['row_5'] += "<span class='label label-info'><a href='/desk#Form/Compensatory Time Off/"+d+"'> "+d+" </a></span>"

				data.append(row)
				row = {}
			data.append({})

	return data