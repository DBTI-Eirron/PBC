from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_schedule, get_holiday_list, get_leave_list, get_shift_map, get_card_within, 
get_attendance, get_defaults, get_ob_list, get_ot_list, get_ut_list, get_ext_list, get_sorted_card, get_suspension_map, get_suspension)

def get_rates(emp):
	monthly_rate = 0.0
	hourly_rate = 0.0
	semi_rate = 0.0
	daily_rate = 0.0
	if emp['rate'] > 0 and  emp['total_yr_days'] > 0 and emp['no_hours'] > 0:
		month_days = (flt(emp['total_yr_days'], 8) / 12)
		if emp['rate_type'] == "Monthly Rate":
			monthly_rate = flt(emp['rate'], 8)
			semi_rate = flt(emp['rate'], 8) / 2
			daily_rate = flt(emp['rate'], 8) / month_days
			hourly_rate = ( flt(emp['rate'], 8) / month_days ) / emp['no_hours']

		elif emp['rate_type'] == "Hourly Rate":
			monthly_rate = ( flt(emp['rate'], 8) * emp['no_hours'] ) * month_days
			semi_rate = ( flt(emp['rate'], 8) * emp['no_hours'] ) * (month_days / 2)
			daily_rate = flt(emp['rate'], 8) * emp['no_hours']
			hourly_rate = flt(emp['rate'], 8)

		elif emp['rate_type'] == "Daily Rate":
			monthly_rate = flt(emp['rate'], 8) * month_days
			semi_rate = flt(emp['rate'], 8) * (month_days / 2)
			daily_rate = flt(emp['rate'], 8)
			hourly_rate = flt(emp['rate'], 8) / emp['no_hours']

	return {
		"monthly_rate": monthly_rate,
		"semi_rate": semi_rate,
		"daily_rate": daily_rate,
		"hourly_rate": flt(hourly_rate, 8)
	}


def get_overtime_map():
	ot_map = {}
	ot = frappe.db.sql(""" SELECT ot_code, ot_rate FROM `tabOvertime Rates` """, as_dict=1)
	for t in ot:
		ot_map[t.ot_code] = {
			"rate": t.ot_rate,
		}
	return ot_map