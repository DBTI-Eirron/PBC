# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import get_timecard_list, get_schedule, get_holiday_list, get_leave_list, get_shift_map, get_card_within, get_attendance

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "target_date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 80
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
			"fieldtype": "Data",
			"width": 140
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
			}
		]

	columns += [
		{
			"fieldname": "card_out",
			"label": _("Time Out"),
			"fieldtype": "Data",
			"width": 140
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

def get_data(filters):
	#Initialize
	data = []

	
	bio, company, worker_hrs, is_attendance_base = frappe.db.get_value("Employee", filters.employee, ["biometrics_id", "company", "no_hours", "is_attendance_base"])
	worker_secs = (worker_hrs * 60) * 60
	pay_from, pay_to = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to"])

	shift_map = get_shift_map()
	timecard_list = get_timecard_list(bio, pay_from, pay_to + datetime.timedelta(days=1))
	schedule = get_schedule(filters.employee, pay_from, pay_to)
	holidays = get_holiday_list(company, pay_from, pay_to)
	leaves = get_leave_list(filters.employee, pay_from, pay_to)

	for sched in schedule:
		#set default entries
		entry = {
			#employe settings
			"employee": filters.employee,
			"worker_hrs": worker_hrs,
			"worker_secs": worker_secs,
			"is_attendance_base": is_attendance_base,
			#schedule settings
			"target_date": datetime.datetime.strftime(sched.datetime_in, '%Y-%m-%d'),
			"work_shift": sched.work_shift,
			"pre_shift": add_to_date(sched.datetime_in, hours= (0 - shift_map[sched.work_shift]['setup_preshift']) ),
			"post_shift": add_to_date(sched.datetime_out, hours=shift_map[sched.work_shift]['setup_postshift']),
			"time_in": sched.datetime_in,
			"time_out": sched.datetime_out,
			"break_start": sched.break_start,
			"break_end": sched.break_end,	
			#shift policy
			"work_hours": sched.work_hours,
			"break_mins": sched.break_mins,
			"grace": shift_map[sched.work_shift]['grace_period'],
			"b_grace": shift_map[sched.work_shift]['b_grace_period'],
			"is_flexible": shift_map[sched.work_shift]['is_flexible'],		
			"is_restday": shift_map[sched.work_shift]['is_restday'],
			"ignore_late": shift_map[sched.work_shift]['ignore_late'],
			#general policy
			"approved_ot_only": filters.approved_ot_only,
			"is_processed": 0,
			#timecard data
			"card_in": "",
			"card_out": "",			
			"break_out": "",
			"break_in": "",
			#basic attendance
			"work": 0.0,
			"late": 0.0,
			"break": 0.0,
			"undertime": 0.0,
			"nightdiff": 0.0,
			"is_absent": 0,
			"is_halfday": 0,
			#applications
			#OT
			"overtime": 0.0,
			"linked_ot": "",
			#LEAVE
			"is_leave": 0,
			"leave_name": "",
			"is_lwop": 0,
			"linked_leave": "",
			#NIGHTDIFF
			"nd_start": sched.nd_start,
			"nd_end": sched.nd_end,
			#OB
			"is_ob": 0,
			"ob": 0.0,
			"linked_ob": "",
			#holiday
			"is_holiday": 0,
			"is_sp_holiday": 0,
			"holiday_name": "",
			"linked_holiday": "",
			"tags": "",		
		}
		#ATTENDANCE
		card_list = get_card_within(entry.get('pre_shift'), entry.get('post_shift'), timecard_list)		
		sorted_card_list = sorted(card_list, key=lambda k: k['card_datetime'])
		for card in sorted_card_list:
			if card['card_type'] == 0:
				if entry['card_in'] == "":
					entry['card_in'] = card['card_datetime']
			elif card['card_type'] == 1:
				entry['card_out'] = card['card_datetime']

			elif card['card_type'] == 2:
				if entry['break_out'] == "":
					entry['break_out'] = card['card_datetime']
			elif card['card_type'] == 3:
				entry['break_in'] = card['card_datetime']

		get_attendance(entry, leaves, holidays)
		entry["tags"] += " <span class='label label-info'>"+ entry['holiday_name'] +"</span>" if entry['is_holiday'] == 1 else ""
		entry["tags"] += " <span class='label label-info'> Special Non-Working </span>" if entry['is_sp_holiday'] == 1 else ""
		entry["tags"] += " <span class='label label-danger'> Late </span> " if entry['late'] > 0 else ""
		entry["tags"] += " <span class='label label-danger'> Undertime </span> " if entry['undertime'] > 0 else ""
		entry["tags"] += " <span class='label label-success'> Overtime </span> " if entry['overtime'] > 0 else ""
		entry["tags"] += " <span class='label label-success'> Official Business </span> " if entry['is_ob'] else ""
		entry["tags"] += " <span class='label label-danger'> Absent </span> " if entry['is_absent'] > 0 else ""
		entry["tags"] += " <span class='label label-danger'> LWOP </span> " if entry['is_lwop'] > 0 else ""
		entry["tags"] += "<span class='label label-success'>"+cstr(entry['leave_name'])+"</span>" if entry['is_leave'] > 0 else ""
		if entry['is_restday']:
			entry["tags"] += "<span class='label label-info'> Rest Day </span> "
		else:
			if not entry['card_in'] and entry['is_attendance_base']:
				entry["tags"] += " <span class='label label-warning'> No Card IN </span> "

			if not entry['card_out'] and entry['is_attendance_base']:
				entry["tags"] += " <span class='label label-warning'> No Card OUT </span> "

		entry['break'] = convert_secs(filters, entry['break'])
		entry['work'] = convert_secs(filters, entry['work'])
		entry['late'] = convert_secs(filters, entry['late'])
		entry['undertime'] = convert_secs(filters, entry['undertime'])
		entry['overtime'] = convert_secs(filters, entry['overtime'])
		data.append(entry)

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)
	return result

def convert_secs(filters, secs):
	con = 0
	if filters.time_options == "Mins":
		con = flt(secs, 8) / 60
	else:
		con = flt(secs, 8) / 3600
	return flt(con, 8)