from __future__ import unicode_literals

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.utils import cint, flt, getdate, cstr, nowdate
from frappe.model.document import Document

def run_patch():
	frappe.db.sql(""" UPDATE `tabWork Shift` SET firsthalf_start = time_in, firsthalf_end = break_start, secondhalf_start = break_end, secondhalf_end = time_out """)
	frappe.db.sql("""UPDATE `tabWork Schedule` firsthalf_start = datetime_in, firsthalf_end = break_start, secondhalf_start = break_end, secondhalf_end = datetime_out """)