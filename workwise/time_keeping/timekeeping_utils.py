from __future__ import unicode_literals
import frappe, datetime
from datetime import time, datetime, timedelta
from frappe.utils import cstr, cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _

def chk_time_format(tm_time, tm_format):
	try:
		try_time = datetime.strptime(tm_time, tm_format).time()
	except ValueError:
		frappe.throw(_("( {0} ) is a not a Valid Time Format should be (Hours:Mins:Seconds) ").format(tm_time))

def str_datetime(tm_time, tm_format):
	new_time = datetime.strptime(tm_time, tm_format)
	return new_time

def str_date(tm_time, tm_format):
	new_time = datetime.strptime(tm_time, tm_format).date()
	return new_time

def str_time(tm_time, tm_format):
	new_time = datetime.strptime(tm_time, tm_format).time()
	return new_times

def add_date(tm_time, tm_format, add_value):
	new_time = datetime.strptime(tm_time, tm_format) + timedelta(days=add_value)
	datetime.strftime(new_time, tm_format)
	return new_time

def sub_date(tm_time, sub_value):
	new_time = tm_time - timedelta(days=sub_value)
	return new_time

def db_datetime_str(tm_time, tm_format):
	new_time = datetime.strftime(tm_time, tm_format)
	return new_time

def timediff_hrs(tm_time1, tm_time2, tm_format):
	time_diff = 0
	time1 = datetime.strptime(tm_time1, tm_format)
	time2 = datetime.strptime(tm_time2, tm_format)
	diff = time1 - time2
	time_diff = abs(diff.total_seconds() / 3600)
	return time_diff

def timediff_mins(tm_time1, tm_time2, tm_format):
	time_diff = 0
	time1 = datetime.strptime(tm_time1, tm_format)
	time2 = datetime.strptime(tm_time2, tm_format)
	diff = time1 - time2
	time_diff = abs(diff.total_seconds() / 60)
	return time_diff

def timediff_raw(tm_time1, tm_time2, tm_format):
	time_diff = 0
	time1 = datetime.strptime(tm_time1, tm_format)
	time2 = datetime.strptime(tm_time2, tm_format)
	timediff = time1 - time2
	return time_diff

def datediff_days(dt_date1, dt_date2, tm_format):
	date_diff = 0
	date1 = datetime.strptime(dt_date1, tm_format)
	date2 = datetime.strptime(dt_date2, tm_format)
	diff = date1 - date2
	date_diff = abs(diff)
	return date_diff

def datediff_days_raw(dt_date1, dt_date2, tm_format):
	date_diff = 0
	date1 = datetime.strptime(dt_date1, tm_format)
	date2 = datetime.strptime(dt_date2, tm_format)
	diff = date1 - date2
	date_diff = diff
	return date_diff

def datetimediff_hrs(tm_time1, tm_time2, tm_format):
	time_diff = 0
	time1 = datetime.strptime(tm_time1, tm_format)
	time2 = datetime.strptime(tm_time2, tm_format)
	diff = time1 - time2
	time_diff = abs(diff.total_seconds() / 3600)
	return time_diff