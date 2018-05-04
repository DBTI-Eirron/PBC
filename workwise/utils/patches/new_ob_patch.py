from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.utils import cint, flt, getdate, cstr, nowdate, get_datetime, add_days
from frappe.model.document import Document
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs, sub_date, timediff_hrs

@frappe.whitelist()
def update_old_obs():
	unupdated_list = frappe.db.sql(""" SELECT `name`,to_time, from_time, travel_time, from_date, total_hrs FROM `tabOfficial Business Application` 
		WHERE `name` NOT IN (SELECT DISTINCT(parent) FROM `tabOfficial Business Application Table`) AND docstatus != 2 """, as_dict=True)
	
	for d in unupdated_list:
		oba = frappe.get_doc("Official Business Application", d.name)
		oba.append("official_business_application_table", {
			"target_date": d.from_date,
			"from_time": d.from_time,
			"to_time": d.to_time,	
			"travel_time": d.travel_time,
			"hrs": d.total_hrs,
		})
		oba.save()



