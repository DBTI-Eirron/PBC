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

#bench execute --args "'2019-01-01', '2019-12-31', 'EMP001', 'Sick Leave', 0, 3" workwise.time_keeping.timekeeping_utils.create_leave_credits
def create_leave_credits(from_date, to_date, employee, leave_type, less, credits):
	employee_name = frappe.db.get_value("Employee", employee, "full_name")
	if to_date:
		valid_to = getdate(to_date)
	else:
		lb_year = getdate(target_date).strftime("%Y")
		valid_to = getdate(_(""+lb_year+"-12-31"))
	
	if less == 1:
		btype = "Less"
	else:
		btype = "Add"

	lb = frappe.new_doc("LB Entry")
	lb.update({
		"employee": employee,
		"employee_name": employee_name,
		"leave_type": leave_type,
		"btype": btype,
		"bfrom": "Execute Script",
		"earned_date": getdate(from_date),
		"valid_from": getdate(from_date),
		"valid_to": valid_to,
		"credits": flt(credits),
	})
	lb.insert()

#bench execute --args "'EMP001', 'Sick Leave', 2,'2019-03-13', '2019-03-14'" workwise.time_keeping.timekeeping_utils.show_balance
def show_balance(employee, leave_type, deduct, from_date, to_date):
	from_balance = ""
	add, less, total_balance = 0, 0, 0

	deduct_to = frappe.get_value("Leave Type", leave_type, "deduct_to")
	if not deduct_to:
		deduct_to = leave_type
	
	bl_entries = frappe.db.sql(""" SELECT employee, employee_name, btype, leave_type, 
		earned_date, valid_from, valid_to, credits
		FROM `tabLB Entry` WHERE employee = %s AND leave_type = %s 
		AND (%s BETWEEN valid_from AND valid_to) AND (%s BETWEEN valid_from AND valid_to) 
		ORDER BY earned_date """, (employee, deduct_to, from_date, to_date), as_dict=True)

	for d in bl_entries:
		if d.btype == "Add":
			total_balance += flt(d.credits)
		else:
			total_balance -= flt(d.credits)

	total_balance = total_balance - flt(deduct)

	total_balance
	print(_(total_balance))
