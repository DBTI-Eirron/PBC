# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money

def delta_to_time(delta_obj):
	time_obj = (datetime.datetime.min + delta_obj).time()
	return time_obj
