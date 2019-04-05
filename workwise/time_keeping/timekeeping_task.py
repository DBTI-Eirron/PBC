from __future__ import unicode_literals
import frappe, datetime, math
from frappe.utils import cint, cstr, flt, nowdate, add_days, getdate, fmt_money, get_datetime, add_to_date
from frappe import _

def get_scheduler():
	pass

def leave_balance_monthly():
	balance_scheds = frappe.db.sql(""" SELECT LB.employee, LB.employee_name, LBS.leave_type, LBS.trigger_on, LBS.credits 
		FROM `tabLeave Balance Setup` LB 
		INNER JOIN `tabLeave Balance Schedule` LBS ON LBS.`parent` = LB.`name` WHERE LBS.trigger_on = 'Every Month' """, as_dict=1)

	now_date = nowdate()
	year_end =getdate(datetime.date(datetime.date.today().year, 12, 31))
	for d in balance_scheds:
		lb = frappe.new_doc("LB Entry")
		lb.update({
			"employee": d.employee,
			"employee_name": d.employee_name,
			"leave_type": d.leave_type,
			"btype": "Add",
			"bfrom": "Schedule Monthly",
			"earned_date": now_date,
			"valid_from": now_date,
			"valid_to": year_end,
			"credits": d.credits
		})
		lb.insert()