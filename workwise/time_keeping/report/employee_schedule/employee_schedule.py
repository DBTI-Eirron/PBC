# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from datetime import timedelta
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import get_schedule

def execute(filters=None):
	columns, results = [], []
	if filters.employee or filters.period_group or filters.location or filters.department or filters.position_title:
		columns = get_columns(filters)
		results = get_result(filters)

	return columns, results

def get_columns(filters):
	columns = [
		{
			"fieldname": "target_date",
			"label": _("Date"),
			"fieldtype": "Data",
			"width": 260
		},
		{
			"fieldname": "work_shift",
			"label": _("Shift"),
			"fieldtype": "Link",
			"options": "Work Shift",
			"width": 180
		},
		#{
		#	"fieldname": "pre_shift",
		#	"label": _("PRE"),
		#	"fieldtype": "Data",
		#	"width": 140
		#},
		{
			"fieldname": "time_in",
			"label": _("Time In"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "break_start",
			"label": _("Break Start"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "break_end",
			"label": _("Break End"),
			"fieldtype": "Data",
			"width": 140
		},	
		{
			"fieldname": "time_out",
			"label": _("Time Out"),
			"fieldtype": "Data",
			"width": 140
		},
		#{
		#	"fieldname": "post_shift",
		#	"label": _("POST"),
		#	"fieldtype": "Data",
		#	"width": 140
		#},
	]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_data(filters):
	#Initialize
	data = []
	employee_schedule = {}
	employee_list = []
	shift_map = {}
	shift_list = []
	template_map = {}
	pay_from, pay_to = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to"])
	pay_to = getdate(pay_to)
	pay_from = getdate(pay_from)
	employees = get_employees(filters)
	if not employees:
		return frappe.throw(_("No Record Found"))

	#Get Work Sched Template
	templates = frappe.db.sql("""SELECT `name`, monday, tuesday, wednesday, thursday, friday, saturday, sunday FROM `tabWork Schedule Template` """,as_dict=True)
	for t in templates:
		template_map[t.name]={
			"0":t.monday,
			"1":t.tuesday,
			"2":t.wednesday,
			"3":t.thursday,
			"4":t.friday,
			"5":t.saturday,
			"6":t.sunday
		}

	#Get Shift Map
	shifts = frappe.db.sql("""SELECT * FROM `tabWork Shift` """, as_dict=True)
	for d in shifts:
		shift_map[d.name] = {
			"work_shift": d['name'],
			"shift_type": d['work_shift_type'],
			"time_in": d['time_in'],
			"time_out": d['time_out'],
			"break_start": d['break_start'],
			"break_end": d['break_end'],
			"pre_shift": add_to_date( d['time_in'], hours = (0 - d['setup_preshift']) ),
			"post_shift": add_to_date( d['time_out'], hours = d['end_postshift'] ),
		}
		shift_list.append(d.name)

	#Set Default
	for emp in employees:
		employee_schedule[emp.name] = {
			"employee_name": cstr(emp.full_name),
			"default_schedule": cstr(emp.default_schedule),
		}
		employee_list.append(emp.name)
		for target_date in daterange(pay_from, pay_to):
			employee_schedule[emp.name][target_date] = None

	#Get Work Schedule
	for emp in employees:
		schedule = frappe.db.sql("""SELECT employee, company, work_shift, target_date, datetime_in, datetime_out, break_start, break_end
			FROM `tabWork Schedule` WHERE target_date >= %(from_date)s AND target_date <= %(to_date)s AND employee = %(employee)s
			ORDER BY target_date ASC""",{
			"from_date": pay_from, "to_date": pay_to, "employee": emp.name,
		}, as_dict=True)
		
		for d in schedule:
			if emp.name in employee_list:
				if employee_schedule[d.employee][d.target_date] == None:
					employee_schedule[d.employee][d.target_date] = {
						"target_date": d['target_date'],
						"work_shift": d['work_shift'],
						"time_in": d['datetime_in'],
						"time_out": d['datetime_out'],
						"break_start": d['break_start'],
						"break_end": d['break_end'],
						"pre_shift": shift_map[d['work_shift']]['pre_shift'],
						"post_shift": shift_map[d['work_shift']]['post_shift'],
					}

	#Get Default Schedule
	for emp in employee_schedule:
		if employee_schedule[emp]['default_schedule']:
			for target_date in daterange(pay_from, pay_to):
				if employee_schedule[emp][target_date] == None:
					template_work_shift = template_map[employee_schedule[emp]['default_schedule']][str(target_date.weekday())]
					employee_schedule[emp][target_date] = {
						"target_date": target_date,
						"work_shift": template_work_shift,
						"time_in": get_date(target_date, shift_map[template_work_shift]['time_in'], shift_map[template_work_shift]['time_out'], shift_map[template_work_shift]['shift_type'], 0),
						"time_out": get_date(target_date, shift_map[template_work_shift]['time_in'], shift_map[template_work_shift]['time_out'], shift_map[template_work_shift]['shift_type'], 1),
						"break_start": get_date(target_date, shift_map[template_work_shift]['break_start'], shift_map[template_work_shift]['break_end'], shift_map[template_work_shift]['shift_type'], 0),
						"break_end": get_date(target_date, shift_map[template_work_shift]['break_start'], shift_map[template_work_shift]['break_end'], shift_map[template_work_shift]['shift_type'], 1),
						"pre_shift": shift_map[template_work_shift]['pre_shift'],
						"post_shift": shift_map[template_work_shift]['post_shift'],
					}

	#Get Change Schedule Application
	cs_apps = frappe.db.sql(""" SELECT CSA.employee, CSA.approved_on, CSAT.target_date, CSAT.new_shift
		FROM `tabChange Schedule Application` CSA INNER JOIN `tabChange Schedule Application Table` CSAT ON CSAT.parent = CSA.`name` 
		WHERE CSA.docstatus = 1 AND CSA.workflow_state = 'Approved' AND CSAT.target_date >= %s AND CSAT.target_date <= %s """,(pay_from, pay_to), as_dict=1)
	for cs in cs_apps:
		if cs.employee in employee_list:
			employee_schedule[cs['employee']][cs['target_date']] = {
				"target_date": cs['target_date'],
				"work_shift": cs['new_shift'],
				"pre_shift": shift_map[cs['new_shift']]['pre_shift'],
				"post_shift": shift_map[cs['new_shift']]['post_shift'],
				"time_in": get_date(cs['target_date'], shift_map[cs['new_shift']]['time_in'], shift_map[cs['new_shift']]['time_out'], shift_map[cs['new_shift']]['shift_type'], 0),
				"time_out": get_date(cs['target_date'], shift_map[cs['new_shift']]['time_in'], shift_map[cs['new_shift']]['time_out'], shift_map[cs['new_shift']]['shift_type'], 1),
				"break_start": get_date(cs['target_date'], shift_map[cs['new_shift']]['break_start'], shift_map[cs['new_shift']]['break_end'], shift_map[cs['new_shift']]['shift_type'], 0),
				"break_end": get_date(cs['target_date'], shift_map[cs['new_shift']]['break_start'], shift_map[cs['new_shift']]['break_end'], shift_map[cs['new_shift']]['shift_type'], 1),
			}

	#Set Data Entry
	for emp in employees:
		entry = {
			"target_date": "<b>"+cstr(emp.name)+": "+cstr(emp.full_name)+"</b>",
			"work_shift": "",
			"time_in": "",
			"time_out": "",
			"break_start": "",
			"break_end": "",
			"pre_shift": "",
			"post_shift": "",
		}
		data.append(entry)
		for target_date in daterange(pay_from, pay_to):
			if employee_schedule[emp.name][target_date] != None:
				entry = {
					"target_date": target_date,
					"work_shift": employee_schedule[emp.name][target_date]['work_shift'],
					"time_in": employee_schedule[emp.name][target_date]['time_in'],
					"time_out": employee_schedule[emp.name][target_date]['time_out'],
					"break_start": employee_schedule[emp.name][target_date]['break_start'],
					"break_end": employee_schedule[emp.name][target_date]['break_end'],
					"pre_shift": "", #employee_schedule[emp.name][target_date]['pre_shift'],
					"post_shift": "", #employee_schedule[emp.name][target_date]['post_shift'],
				}
				data.append(entry)
		data.append({})

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = {
			"target_date": d.get("target_date"),
			"work_shift": d.get("work_shift"),
			"pre_shift": d.get("pre_shift"),
			"post_shift": d.get("post_shift"),
			"time_in": d.get("time_in"),
			"time_out": d.get("time_out"),
			"break_start": d.get("break_start"),			
			"break_end": d.get("break_end"),
		}
		
		result.append(row)
	return result

def daterange(start_date, end_date):
    for n in range( int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def get_date(date, start, end, type, is_end):
	if is_end == 1:
		if delta_to_time(start) > delta_to_time(end):
			dt = (datetime.datetime.combine(date, delta_to_time(end) ) + timedelta(days=1) ).strftime('%Y-%m-%d %H:%M:%S')
		else:
			dt = datetime.datetime.combine(date, delta_to_time(end) ).strftime('%Y-%m-%d %H:%M:%S') 
	else:
		dt = datetime.datetime.combine(date, delta_to_time(start) ).strftime('%Y-%m-%d %H:%M:%S') 

	return dt

def delta_to_time(delta_obj):
		return (datetime.datetime.min + delta_obj).time()

def get_employees(filters):
	register = frappe.db.sql("""SELECT TE.`name`, TE.`full_name`, TE.`default_schedule` FROM `tabEmployee` TE
		LEFT JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name`
		WHERE TE.is_active = 1 AND TE.company = %(company)s {conditions} ORDER BY TE.full_name """.format(conditions=get_conditions(filters)), filters, as_dict=1)

	return register

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("TE.`name`='{0}'".format(filters.employee))

	if filters.get("period_group"):
		conditions.append("TE.period_group='{0}'".format(filters.period_group))

	if filters.get("position_title"):
		conditions.append("TE.`position_title`='{0}'".format(filters.position_title))

	if filters.get("department"):
		lft, rgt = frappe.db.get_value("Department", filters.department, ["lft", "rgt"])
		conditions.append(_("( DEPT.`lft` BETWEEN '{0}' AND '{1}' )").format(lft, rgt))

	if filters.get("location"):
		conditions.append("TE.`location`='{0}'".format(filters.location))

	strict_period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')
	if strict_period_group:
		period_group = frappe.db.get_value("Payroll Period", filters.payroll_period, ["period_group"])
		conditions.append("TE.period_group='{0}'".format(period_group))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 