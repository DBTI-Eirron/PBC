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
			"fieldname": "shift",
			"label": _("Shift"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "pre_shift",
			"label": _("POST"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "post_shift",
			"label": _("PRE"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "time_in",
			"label": _("Time IN"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "card_in",
			"label": _("Card IN"),
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
			"fieldname": "break_out",
			"label": _("Break Out"),
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
			"fieldname": "break_in",
			"label": _("Break IN"),
			"fieldtype": "Data",
			"width": 140
		},		
		{
			"fieldname": "time_out",
			"label": _("Time Out"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "card_out",
			"label": _("Card Out"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "late_mins",
			"label": _("Mins Late"),
			"fieldtype": "Float",
			"width": 80
		},
		{
			"fieldname": "is_rest_day",
			"label": _("RD"),
			"fieldtype": "Data",
			"width": 50
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

def get_schedule(filters, pay_from, pay_to):
	schedule = frappe.db.sql("""SELECT * FROM `tabWork Schedule` 
		WHERE employee = %(employee)s AND target_date >= %(from_date)s AND target_date <= %(to_date)s
		ORDER BY target_date ASC""",{
			"employee": filters.employee,
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)

	return schedule

def get_data(filters):
	#Initialize
	data = []
	total_late_hours = 0
	total_late_mins = 0

	bio = frappe.db.get_value("Employee", filters.employee, "biometrics_id")
	pay_from, pay_to = frappe.db.get_value("Payroll Period", filters.payroll_period, ["from_date", "to_date"])

	timecard_list = get_timecard_list(filters, bio, pay_from, pay_to + datetime.timedelta(days=1))
	schedule = get_schedule(filters, pay_from, pay_to)

	
	for sched in schedule: 
		entry = {
			"time_in": sched.datetime_in,
			"time_out": sched.datetime_out,
			"pre_shift": sched.pre_shift,
			"post_shift": sched.post_shift,
			"card_in": "",
			"card_out": "",
			"break_start": sched.break_start,
			"break_end": sched.break_end,			
			"break_out": "",
			"break_in": "",
			"worked_hrs": 0.0,
			"late_mins": 0.0,
			"late_hours": 0.0,
			"is_rest_day": 0,
			"tags": "",
		}

		#ATTENDANCE
		card_list = get_card_within(sched.pre_shift, sched.post_shift, timecard_list)		
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

		#RESTDAY
		if (sched.is_rest_day == 1):
			entry['is_rest_day'] = 1		
		data.append(entry)
	
	data.append({
			"datetime_in": _("TOTAL"),
			"late_mins": total_late_mins,
			"late_hours": total_late_hours,
		})

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = {
			"date": d.get("target_date"),
			"pre_shift": d.get("pre_shift"),
			"post_shift": d.get("post_shift"),
			"time_in": d.get("time_in"),
			"card_in": d.get("card_in"),
			"time_out": d.get("time_out"),
			"card_out": d.get("card_out"),
			"break_start": d.get("break_start"),			
			"break_end": d.get("break_end"),
			"break_out": d.get("break_out"),
			"break_in": d.get("break_in"),			
			"late_mins": d.get("late_mins"),
			"late_hours": d.get("late_hours"),
			"is_rest_day": d.get("is_rest_day"),
			"tags": d.get("tags"),
		}
		
		result.append(row)
	return result

def get_time_in(filters, bio, pay_from, pay_to, sched):
	timecard_list = frappe.db.sql("""SELECT TIMESTAMP(date, time) as card_data, card_type FROM `tabTime Card` 
		WHERE biometrics_id = %(bio)s AND date >= %(from_date)s AND date <= %(to_date)s
		ORDER BY date, time """,{
			"bio": bio,
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)
	return timecard_list

def get_card_within(pre_shift, post_shift, timecard_list):
	cards = []
	for tc in timecard_list:
		if pre_shift <= tc.card_datetime <= post_shift:
			cards.append({
				'card_datetime': tc.card_datetime,
				'card_type': tc.card_type
			})

	#frappe.throw(_("{0}").format( post_shift ))		

	return cards

def get_timecard_list(filters, bio, pay_from, pay_to):
	timecard_list = frappe.db.sql("""SELECT TIMESTAMP(date, time) as card_datetime, card_type FROM `tabTime Card` 
		WHERE biometrics_id = %(bio)s AND date >= %(from_date)s AND date <= %(to_date)s
		ORDER BY date, time """,{
			"bio": bio,
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)
	return timecard_list