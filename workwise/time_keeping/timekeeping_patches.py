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
	application_list = frappe.db.sql(""" SELECT `name`, old_shift, new_shift, target_date, new_time_in, new_time_out FROM `tabChange Schedule Application` WHERE docstatus = 1; """, as_dict=1)
	existing_list = frappe.db.sql(""" SELECT `parent` FROM `tabChange Schedule Application Table` GROUP BY `parent`; """, as_list=1)

	for app in application_list:
		if app.name not in existing_list:
			frappe.db.sql(""" INSERT INTO `tabChange Schedule Application Table` 
				( `name`, `creation`,`modified`,`owner`,docstatus,`parent`,`parentfield`,`parenttype`,`idx`,`time_in`,`time_out`,`new_shift`,`current_shift`,`target_date`) VALUES
				(  lpad(conv(floor(rand()*pow(36,6)), 10, 36), 10, 0),  NOW(), NOW(), 'Administrator', 1, %s, 'change_list', 'Change Schedule Application', 1, %s, %s, %s, %s, %s) """,( app.name, app.new_time_in, app.new_time_out, app.new_shift, app.old_shift, app.target_date ))
			frappe.db.commit()

def oba_update_table():
	frappe.db.sql("""UPDATE `tabOfficial Business Application Table` SET travel_time = travel_time, hrs = hrs, target_date = target_date, `date` = `target_date`, from_time = from_time, to_time = to_time, is_holiday = is_holiday, is_excluded = is_excluded, is_previous = 0 WHERE `date` IS NULL AND docstatus != 2 """)
	frappe.db.commit()

	frappe.db.sql("""UPDATE `tabOfficial Business Application Table`  SET `to_date` = `date` WHERE to_date IS NULL """)
	frappe.db.commit()

def oba_trigger_save():
	oba = frappe.db.sql(""" SELECT `name` FROM `tabOfficial Business Application` WHERE docstatus = 0 AND workflow_state = "Pending" """, as_dict=1)
	for b in oba:
		application = frappe.get_doc("Official Business Application", b.name)
		application.save()

def transfer_tksettings_to_workshift():
	tk_settings = frappe.db.sql(""" SELECT DISTINCT * FROM `tabSingles` WHERE `doctype` = "Timekeeping Settings" """, as_dict=1)
	if tk_settings:
		frappe.db.sql(""" UPDATE `tabWork Shift` SET min_ot_hrs = %s, max_ot_hrs = %s, max_ot_break = %s, cto_min_filing_hrs = %s, cto_max_filing_hrs = %s """, (tk_settings[0].req_ot, tk_settings[0].ot_max_hours, tk_settings[0].ot_max_break, tk_settings[0].cto_min_hrs, tk_settings[0].cto_max_hrs))
		frappe.db.commit()

#DELETE COMPANY RECORDS
def qetquery_delete_company_records():
	query_list = []
	format2 = ""
	format1 = ""
	company = ["Opensoft Solutions Inc.", "Triplewell Construction Corporation"]
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
	company = ["Opensoft Solutions Inc.", "Triplewell Construction Corporation"]
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

#Payroll Patch
def update_loan_applications():
	frappe.db.sql("""UPDATE `tabLoan Application` SET freq_method="Automatic" WHERE freq_method IS NULL""")
	frappe.db.commit()

#Employee
def save_employee():
	emp = frappe.db.sql(""" SELECT `name` FROM `tabEmployee` """, as_dict=1)
	for b in emp:
		application = frappe.get_doc("Employee", b.name)
		application.save()

def update_employee_movement():
	frappe.db.sql(""" UPDATE `tabEmployee Movement` EM INNER JOIN `tabEmployee` TE ON EM.employee=TE.`name` SET EM.company=TE.company WHERE EM.company IS NULL """)
	frappe.db.commit()

def add_subordinates_from_employee():
	to_insert_list = []
	cur_sub_list = []

	emp_list = frappe.db.sql(""" SELECT * FROM `tabEmployee` """, as_dict=1)
	if emp_list:
		for emp in emp_list:
			if emp.reports_to:
				to_insert_list.append(str(emp.reports_to))
			emp_approvers = frappe.db.sql(""" SELECT * FROM `tabEmployee Approvers` WHERE `parent`=%s """,(emp.name), as_dict=1)
			if emp_approvers:
				for a in emp_approvers:
					to_insert_list.append(str(a.approver))
		if to_insert_list:
			to_insert_list = list( dict.fromkeys(to_insert_list) )

		cur_sub = frappe.db.sql(""" SELECT DISTINCT `name` FROM `tabEmployee Subordinates` """, as_dict=1)
		if cur_sub:
			for cur in cur_sub:
				cur_sub_list.append(cur.name)

		for e in emp_list:
			for ins in to_insert_list:
				if ins in cur_sub_list:
					frappe.db.sql(""" INSERT INTO `tabSubordinates` (`name`, `creation`, `modified`, `docstatus`, `parent`, `parentfield`, `parenttype`, `idx`, `subordinate_name`, `subordinate`, `created_from_employee`) 
						VALUES (conv(floor(rand() * 99999999999999), 20, 36), NOW(), NOW(), 0, %s, 'subordinates', 'Employee Subordinates', 1, %s, %s, %s) """,(
						ins,
						e.full_name,
						e.name,
						e.name,
					),as_dict=1)
					frappe.db.commit()
				else:
					employee, employee_name, company = frappe.db.get_value("Employee", ins, ["name", "full_name", "company"])
					empsub_new_doc = frappe.new_doc("Employee Subordinates")
					empsub_new_doc.update({
						"employee": employee,
						"employee_name": employee_name,
						"company": company,
					})	
					empsub_new_doc.append('subordinates',{
						"subordinate": e.name,
						"subordinate_name": e.full_name,
						"created_from_employee": e.name,
					})
					empsub_new_doc.insert()
					frappe.db.commit()

def save_employee_subordinates():
	new_sub = frappe.db.sql(""" SELECT DISTINCT `name` FROM `tabEmployee Subordinates` """, as_dict=1)
	if new_sub:
		for new in new_sub:
			application = frappe.get_doc("Employee Subordinates", new.name)
			application.save()
			#frappe.db.commit()

def run_dtrp_applications():
	dtr_list = frappe.db.sql(""" SELECT DA.`name`, DA.`target_date`, DA.`employee`, DA.`is_previous`, TE.`biometrics_id` 
		FROM `tabDTR Problem Application` DA INNER JOIN `tabEmployee` TE ON DA.employee = TE.`name` 
		WHERE DA.`workflow_state` = "Approved" AND DA.`approved_on` >= "2019-06-07" """, as_dict=1)

	for dt in dtr_list:
		dtr_table = frappe.db.sql(""" SELECT `type`, `request` FROM `tabDTR Problem Table` WHERE `action` = "Approved" AND parent = %s """,(dt.name), as_dict=1)
		for d in dtr_table:
			if d.type == "Time In":
				card_type = 0
			if d.type == "Time Out":
				card_type = 1
			if d.type == "Break In":
				card_type = 2
			if d.type == "Break Out":
				card_type = 3

			timecard_sel = frappe.db.sql("""SELECT TC.`name` FROM `tabTime Card` TC JOIN `tabEmployee` TE 
				WHERE TC.biometrics_id = TE.biometrics_id  AND TC.`date` = %s AND TC.`card_type` = %s 
				AND TE.`name` = %s LIMIT 1 """, (getdate(dt.target_date), card_type, dt.employee), as_dict=True)
			if timecard_sel:
				frappe.db.sql(""" UPDATE `tabTime Card` SET `time`=%s WHERE `name` = %s """,(d.request, timecard_sel[0].name))
				frappe.db.commit()
			else:
				if dt.is_previous > 0:
					target_date = dt.target_date - datetime.timedelta(days=1)
				else:
					target_date = dt.target_date

				new_timecard = frappe.new_doc("Time Card")
				new_timecard.update({
					"biometrics_id": dt.biometrics_id,
					"card_type": card_type,
					"date": str(target_date),
					"time": str(d.request)
				})

				new_timecard.insert(ignore_permissions = True)
				new_timecard.save(ignore_permissions = True)
				frappe.db.commit()

def run_change_schedule_applications():
	csa_list = frappe.db.sql(""" SELECT CA.`employee`, CA.`company`, CT.`target_date`, CT.`current_shift`, CT.`new_shift` 
		FROM `tabChange Schedule Application Table` CT INNER JOIN `tabChange Schedule Application` CA ON CT.`parent`=CA.`name` 
		WHERE CA.`workflow_state` = "Approved" AND CA.`docstatus` = 1 AND CA.`approved_on` = "2019-06-26" """, as_dict=True)

	for csa in csa_list:
		old_shift = ""
		work_shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(csa.new_shift), as_dict=True)
		
		exist = frappe.db.sql("""SELECT `name` FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (csa.employee, csa.target_date), as_dict=True)
		if exist:
			frappe.db.sql("""DELETE FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s """, (csa.employee, csa.target_date), as_dict=True)
			frappe.db.commit()
			
		old_shift = frappe.db.sql_list("""SELECT `work_shift` FROM `tabWork Schedule` WHERE employee = %s AND target_date = %s LIMIT 1""", (csa.employee, csa.target_date))
		target_date = getdate(csa.target_date)

		for ws in work_shift:
			work_sched = frappe.new_doc("Work Schedule")
			work_sched.update({
				"employee": csa.employee,
				"company": csa.company,
				"target_date": csa.target_date,
				"work_shift": ws.name,
				"shift_type": ws.work_shift_type,
				"work_hours": ws.work_hours,
				"break_mins": ws.break_mins,
				"datetime_in": get_date(csa.target_date, ws.time_in, ws.time_out, ws.work_shift_type, 0), 
				"datetime_out": get_date(csa.target_date, ws.time_in, ws.time_out, ws.work_shift_type, 1),			
				"break_start": get_date(csa.target_date, ws.break_start, ws.break_end, ws.work_shift_type, 0),
				"break_end": get_date(csa.target_date, ws.break_start, ws.break_end, ws.work_shift_type, 1),
				"nd_start": get_date(csa.target_date, ws.nd_start, ws.time_out, ws.nd_end, 0),
				"nd_end": get_date(csa.target_date, ws.nd_start, ws.time_out, ws.nd_end, 1),
			})
			work_sched.insert()
			frappe.db.commit()

def update_override():
	all_sched = frappe.db.sql("""SELECT `employee`,`target_date`,`o_time_in`,`o_break_in`,`o_break_out`,`o_time_out` FROM `tabWork Schedule` WHERE `o_time_in` <> NULL OR `o_break_in` <> NULL OR `o_break_out` <> NULL OR `o_time_out`""",as_dict=True)
	for s in all_sched:
		override = frappe.new_doc("Override List")
		override.update({
			"name":s.employee+" "+str(s.target_date),
			"employee":s.employee,
			"target_date": s.target_date,
		})
		if s.o_time_in:
			override.update({
				"time_in":s.o_time_in
			})
		if s.o_break_in:
			override.update({
				"break_in":s.o_break_in
			})
		if s.o_break_out:
			override.update({
				"break_out":s.o_break_out
			})
		if s.o_time_out:
			override.update({
				"time_out":s.o_time_out
			})
		override.save()

def update_split_govt():  #1.0.61
	tt = frappe.db.sql("""SELECT `name` FROM `tabTransaction Type` WHERE is_government = 1 """,as_dict=True)
	for t in tt:
		document = frappe.get_doc("Transaction Type", t.name)
		document.update({
			"is_sss": 1,
		})
		document.save()

def update_split_govt_all(): #1.0.61
	tt = frappe.db.sql("""SELECT `name` FROM `tabTransaction Type` WHERE is_government = 1 """,as_dict=True)
	for t in tt:
		document = frappe.get_doc("Transaction Type", t.name)
		document.update({
			"is_sss": 1,
			"is_hdmf": 1,
			"is_phic": 1,
		})
		document.save()

def update_cardtype_in_dtrp(): #1.0.62
	frappe.db.sql(""" UPDATE `tabDTR Problem Table`
		SET card_type= CASE
		   WHEN `type`='Time In' THEN 0
		   WHEN `type`='Time Out' THEN 1
			 WHEN `type`='Break Out' THEN 2
			 WHEN `type`='Break In' THEN 3
		END """,as_dict=True)

def cto_fix(): #For Rephil Only
	used_cto_dict = {}
	uc_cnt = 0
	ent_cnt = 0

	used_cto_list = frappe.db.sql(""" SELECT * FROM `tabCompensatory Time Off` CO WHERE  CO.`type` = 'Use' AND CO.`workflow_state` = 'Approved' AND CO.`required_credits` > 0 """, as_dict=1)
	for uc in used_cto_list:
		uc_cnt += 1
		entries = []
		req_credits = flt(uc.required_credits, 2)
		req_cr = 0.00
		ucto_trans = frappe.db.sql(""" SELECT * FROM `tabCompensatory Time Off Table` WHERE `parent` = %s """,(uc.name), as_dict=1)
		for trn in ucto_trans:
			req_cr += trn.credits_used

		if flt(req_credits, 2) != flt(req_cr, 2):
			filed_ctos = frappe.db.sql(""" SELECT * FROM `tabCompensatory Time Off` WHERE `employee` = %s AND `balance` > 0 AND `type` = 'FILE' AND `workflow_state` = 'Approved' GROUP BY `name` 
			ORDER BY `employee`, `date` DESC """,(uc.employee), as_dict=1)
			for a in filed_ctos:
				cred_used = 0.0
				if a.balance > 0:
					if req_credits > 0: 
						if flt(a.balance, 2) >= req_credits:
							remain_bal = flt(a.balance, 2) - req_credits
							cred_used = flt(a.credits_used, 2) + req_credits
							req_credits = 0.0
						else:
							remain_bal = 0.0
							req_credits = req_credits - flt(a.balance, 2)
							cred_used = flt(a.balance, 2)
						
						row = {
							"cto_name": str(uc.name),
							"filed_cto": a.name,
							"date": a.date,
							"balance": flt(a.balance, 2),
							"credits_used": cred_used - flt(a.balance, 2) if cred_used > a.balance else cred_used
						}
						entries.append(row);
						
						frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET `balance` = %s, credits_used = %s WHERE `name` = %s AND docstatus = 1 AND `workflow_state` = "Approved" """, (remain_bal, cred_used, a.name))
						frappe.db.commit()
				else:
					break

		if entries:
			for ent in entries:
				ent_cnt += 1
				transaction = frappe.new_doc("Compensatory Time Off Table")
				transaction.update({
					"filed_cto": ent['filed_cto'],
					"date": ent['date'],
					"balance": ent['balance'],
					"credits_used":ent['credits_used'],
					"docstatus": 1,
					"parent": ent['cto_name'],
					"parentfield": 'use_cto_table',
					"parenttype": 'Compensatory Time Off',
				})
				transaction.insert()
				frappe.db.commit()

def cto_transaction_fix(): #For Rephil Only
	fix_filed_cto = frappe.db.sql(""" UPDATE `tabCompensatory Time Off` SET credits_earned=total_hours/8 WHERE credits_earned <= 0 AND type = 'File' """)
	frappe.db.commit()

	use_cto_list = frappe.db.sql(""" SELECT CO.`name`, CO.`employee` FROM `tabCompensatory Time Off` CO
	WHERE CO.`workflow_state` = 'Approved' AND CO.`type` = 'Use' """, as_dict=1)

	for use in use_cto_list:
		use_transaction = frappe.db.sql(""" SELECT * FROM `tabCompensatory Time Off Table` WHERE `parent` = %s """,(use.name), as_dict=1)
		for trn in use_transaction:
			if trn.name != use.name:
				filed_cto_list = frappe.db.sql(""" SELECT `name` FROM `tabCompensatory Time Off` WHERE `name` = %s AND type = 'File' LIMIT 1 """,(trn.filed_cto), as_dict=1)
				for a in filed_cto_list:
					if use.employee != a.employee:
						frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET credits_used = credits_used - %s WHERE `name` = %s AND docstatus = 1 AND `workflow_state` = "Approved" """, (trn.credits_used, trn.filed_cto))
						frappe.db.commit()

						frappe.db.sql("""UPDATE `tabCompensatory Time Off` SET `balance` = (credits_earned - credits_used) WHERE `name` = %s AND docstatus = 1 AND `workflow_state` = "Approved" """, (trn.filed_cto))
						frappe.db.commit()

						frappe.db.sql(""" DELETE FROM `tabCompensatory Time Off Table` WHERE filed_cto = %s AND `date` = %s """, (trn.filed_cto, trn.date))
						frappe.db.commit()