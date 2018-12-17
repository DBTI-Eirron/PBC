from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _

def update_approved_on_and_by():
	application_type_list = ["Official Business Application", "Leave Application", "Overtime Application", "Change Schedule Application", "Excuse Tardiness Application", "Undertime Application", "Compensatory Time Off", "DTR Problem Application"]
	for app in application_type_list:
		table = "`tab"+app+"`"
		table = str(table)

		application_list = frappe.db.sql(""" SELECT `name`, DATE(modified) as date, modified_by FROM """+table+""" WHERE docstatus = 1 AND approved_on IS NULL AND approved_by IS NULL """, as_dict=1)
		for a in application_list:
			frappe.db.sql("""UPDATE """+table+""" SET `approved_on` = DATE(modified), approved_by = modified_by WHERE `docstatus` = 1 AND `name` = %s """, (a.name))
			frappe.db.commit()

def update_old_change_schedule_application():
	frappe.db.sql("""UPDATE `tabChange Schedule Application` SET `posting_date` = DATE(creation) WHERE `docstatus` = 1 AND `posting_date` IS NULL """)
	frappe.db.commit()

def oba_update_table():
	frappe.db.sql("""UPDATE `tabOfficial Business Application Table` SET travel_time = travel_time, hrs = hrs, target_date = target_date, `date` = `target_date`, from_time = from_time, to_time = to_time, is_holiday = is_holiday, is_excluded = is_excluded, is_previous = 0 WHERE `date` IS NULL AND docstatus != 2 """)
	frappe.db.commit()

def qetquery_delete_company_records():
	query_list = []
	format2 = ""
	format1 = ""
	company = ["Direc Business Solutions Inc.", "Direc Business Technologies Inc."]
	doctype_list = frappe.db.sql(""" SELECT DISTINCT `name` FROM `tabDocType` WHERE issingle = 0 AND istable = 0 AND `name` IN (SELECT DISTINCT parent FROM `tabDocField` WHERE fieldname = "company") """, as_dict=1)

	if doctype_list:
		for doc in doctype_list:
			table = "`tab"+doc.name+"`"
			table = str(table)

			for com in company:
				to_del = frappe.db.sql(""" SELECT DISTINCT `name` FROM """+table+""" WHERE company = %s """,(com), as_dict=1)
				if to_del:
					has_childtable = frappe.db.sql(""" SELECT DISTINCT `options` FROM `tabDocField` WHERE fieldtype = "Table" AND `parent` = %s LIMIT 1 """,(doc.name), as_dict=1)
					if has_childtable:
						for to in to_del:
							child_table = "`tab"+has_childtable[0].options+"`"
							child_table = str(child_table)
							format2 = "'"+com+"'"
				
						to_app = str(" DELETE T1, T2 FROM "+table+" T1 JOIN "+child_table+" T2 ON T1.`name` = T2.parent WHERE T1.company = "+format2+";")
						query_list.append(to_app)
					
					format2 = "'"+com+"'"
					to_append = str(" DELETE FROM "+table+" WHERE company ="+format2+";")
					query_list.append(to_append)

					to_appnd = str(" DELETE FROM `tabCompany` WHERE `name` ="+format2+";")
					query_list.append(to_appnd)
	
	frappe.throw(_(''.join(query_list)))

def delete_company_records():
	company = ["Direc Business Solutions Inc.", "Direc Business Technologies Inc."]
	doctype_list = frappe.db.sql(""" SELECT DISTINCT `name` FROM `tabDocType` WHERE issingle = 0 AND istable = 0 AND `name` IN (SELECT DISTINCT parent FROM `tabDocField` WHERE fieldname = "company") """, as_dict=1)

	if doctype_list:
		for doc in doctype_list:
			table = "`tab"+doc.name+"`"
			table = str(table)

			for com in company:
				to_del = frappe.db.sql(""" SELECT DISTINCT `name` FROM """+table+""" WHERE company = %s """,(com), as_dict=1)
				if to_del:
					has_childtable = frappe.db.sql(""" SELECT DISTINCT `options` FROM `tabDocField` WHERE fieldtype = "Table" AND `parent` = %s LIMIT 1 """,(doc.name), as_dict=1)
					if has_childtable:
						for to in to_del:
							child_table = "`tab"+has_childtable[0].options+"`"
							child_table = str(child_table)
						
						frappe.db.sql("""DELETE T1, T2 FROM """+table+""" T1 JOIN """+child_table+""" T2 ON T1.`name` = T2.parent WHERE T1.company = %s """,(com))
						frappe.db.commit()
					
					frappe.db.sql("""DELETE FROM """+table+""" WHERE company = %s """,(com))
					frappe.db.commit()

				frappe.db.sql("""DELETE FROM `tabCompany` WHERE `name` = %s """,(com))
				frappe.db.commit()