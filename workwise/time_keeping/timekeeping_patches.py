from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, cstr
from frappe import _

#APPLICATION PATCHES
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

	frappe.db.sql("""UPDATE `tabOfficial Business Application Table`  SET `to_date` = `date` WHERE to_date IS NULL """)
	frappe.db.commit()

	oba = frappe.db.sql(""" SELECT `name` FROM `tabOfficial Business Application` WHERE docstatus = 0 AND workflow_state = "Pending" """, as_dict=1)
	for b in oba:
		application = frappe.get_doc("Official Business Application", b.name)
		application.save()

#DELETE COMPANY RECORDS
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

#REASSIGN WORK SCHEDULE
def delta_to_time(delta_obj):
	return (datetime.datetime.min + delta_obj).time()

def get_date(date, start, end, type, is_end):
	if is_end == 1:
		if delta_to_time(start) > delta_to_time(end):
			dt = (datetime.datetime.combine(date, delta_to_time(end) ) + datetime.timedelta(days=1) ).strftime('%Y-%m-%d %H:%M:%S')
		else:
			dt = datetime.datetime.combine(date, delta_to_time(end) ).strftime('%Y-%m-%d %H:%M:%S') 
	else:
		dt = datetime.datetime.combine(date, delta_to_time(start) ).strftime('%Y-%m-%d %H:%M:%S') 

	return dt

def reassign_work_schedule():
	existing = frappe.db.sql("""SELECT `name`, target_date, work_shift FROM `tabWork Schedule` """, as_dict=True)
	if existing:
		for d in existing:
			shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(d.work_shift), as_dict=True)
			if shift:
				frappe.db.sql(""" UPDATE `tabWork Schedule` SET 
					work_shift = %(work_shift)s,
					shift_type = %(shift_type)s,
					work_hours = %(work_hours)s,
					break_mins = %(break_mins)s,
					datetime_in = %(datetime_in)s,
					datetime_out = %(datetime_out)s,
					break_start = %(break_start)s,
					break_end = %(break_end)s,
					nd_start = %(nd_start)s,
					nd_end = %(nd_end)s
					WHERE `name` = %(doc_name)s """, { 
					"work_shift": shift[0]['name'],
					"shift_type": shift[0]['work_shift_type'],
					"work_hours": shift[0]['work_hours'],
					"break_mins": shift[0]['break_mins'],
					"datetime_in": get_date(d.target_date, shift[0]['time_in'], shift[0]['time_out'], shift[0]['work_shift_type'], 0), 
					"datetime_out": get_date(d.target_date, shift[0]['time_in'], shift[0]['time_out'], shift[0]['work_shift_type'], 1),
					"break_start": get_date(d.target_date, shift[0]["break_start"], shift[0]["break_end"], shift[0]['work_shift_type'], 0),
					"break_end": get_date(d.target_date, shift[0]["break_start"], shift[0]["break_end"], shift[0]['work_shift_type'], 1),
					"nd_start": get_date(d.target_date, shift[0]["nd_start"], shift[0]['time_out'], shift[0]["nd_end"], 0),
					"nd_end": get_date(d.target_date, shift[0]["nd_start"], shift[0]['time_out'], shift[0]["nd_end"], 1),
					"doc_name": d.name
				}, as_dict=True)
				frappe.db.commit()