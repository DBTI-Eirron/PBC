from __future__ import unicode_literals
import frappe, datetime, math
from frappe.utils import cint, cstr, flt, nowdate, add_days, getdate, fmt_money, get_datetime, add_to_date
from frappe import _

def get_scheduler():
	pass

def leave_balance_monthly():
	balance_scheds = frappe.db.sql(""" SELECT LB.employee, LB.employee_name, LBS.leave_type, LBS.trigger_on, LBS.credit 
		FROM `tabLeave Balance` LB 
		INNER JOIN `tabLeave Balance Schedule` LBS ON LBS.`parent` = LB.`name` WHERE LBS.trigger_on = 'Every Month' """, as_dict=1)

	for d in balance_scheds:
		pass



