from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _

def update_approved_on_and_by():
	application_type_list = ["Official Business Application", "Leave Application", "Overtime Application", "Change Schedule Application"]
	for app in application_type_list:
		table = "`tab"+app+"`"
		table = str(table)

		application_list = frappe.db.sql(""" SELECT `name`, DATE(modified) as date, modified_by FROM """+table+""" WHERE docstatus = 1 AND approved_on IS NULL AND approved_by IS NULL """, as_dict=1)
		for a in application_list:
			frappe.db.sql("""UPDATE """+table+""" SET `approved_on` = DATE(modified), approved_by = modified_by WHERE `docstatus` = 1 AND `name` = %s """, (a.name))
			frappe.db.commit()