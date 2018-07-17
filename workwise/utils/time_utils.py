from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _

def check_time_format(time):
	try:
		try_time = datetime.strptime(time ,"%H:%M").time()
	except ValueError:
		try:
			try_time = datetime.strptime(time, "%H:%M:%S").time()
		except ValueError:
			frappe.throw(_("( {0} ) is a not a Valid Time Format").format( self.get(fd) ))

def get_time_diff(time):
	try:
		try_time = datetime.strptime(time ,"%H:%M").time()
	except ValueError:
		try:
			try_time = datetime.strptime(time, "%H:%M:%S").time()
		except ValueError:
			frappe.throw(_("( {0} ) is a not a Valid Time Format").format( self.get(fd) ))