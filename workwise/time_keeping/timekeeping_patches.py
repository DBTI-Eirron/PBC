from __future__ import unicode_literals
import frappe, datetime, calendar
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, cstr, today
from workwise.time_keeping.attendance_utils import get_schedule
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs
from frappe import _

#APPLICATION PATCHES
def update_cost_center_company():
	cc_dict = frappe.db.sql("""SELECT `name`, lft, rgt, parent_cost_center FROM `tabCost Center`""",as_dict=True)
	direct = []
	child = []
	for cc in cc_dict:
		if cc.parent_cost_center == "Cost Center Structure":
			direct.append({"name":cc.name,"lft":cc.lft,"rgt":cc.rgt})
		if cc.parent_cost_center is not None:
			child.append({"name":cc.name,"lft":cc.lft,"rgt":cc.rgt})

	for cost in child:
		for center in direct:
			if center['lft'] <= cost['lft'] and center['rgt'] >= cost['rgt']:
				frappe.db.sql("""UPDATE `tabCost Center` SET company = %s WHERE name = %s""",(center['name'],cost['name']))

def update_approved_on_and_by():
	application_type_list = ["Official Business Application", "Leave Application", "Overtime Application", "Change Schedule Application", "Excuse Tardiness Application", "Undertime Application", "Compensatory Time Off", "DTR Problem Application", "Timelogs Application"]
	for app in application_type_list:
		table = "`tab"+app+"`"
		table = str(table)

		if app in ['DTR Problem Application', 'Change Schedule Application', 'Timelogs Application']:
			frappe.db.sql("""UPDATE """+table+""" APP SET APP.`approved_on`=APP.`modified`, APP.`approved_by`=APP.`modified_by`, 
			APP.`approver_name`=(SELECT TE.`full_name` FROM `tabEmployee` TE WHERE TE.`user_id`=APP.modified_by LIMIT 1) 
			WHERE APP.`docstatus` = 1 AND APP.`workflow_state` IN ('Approved', 'Approval in Progress') AND (APP.approved_on IS NULL OR APP.approved_by IS NULL) """)
		else:
			frappe.db.sql("""UPDATE """+table+""" APP SET APP.`approved_on`=DATE(APP.`modified`), APP.`approved_by`=APP.`modified_by`, 
			APP.`approver_name`=(SELECT TE.`full_name` FROM `tabEmployee` TE WHERE TE.`user_id`=APP.modified_by LIMIT 1) 
			WHERE APP.`docstatus` = 1 AND APP.`workflow_state` IN ('Approved', 'Approval in Progress') AND (APP.approved_on IS NULL OR APP.approved_by IS NULL) """)
			
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

def cto_hard_reset():
	fix_filed_cto = frappe.db.sql(""" UPDATE `tabCompensatory Time Off` SET balance=credits_earned, credits_used=0 WHERE `type` = 'File' """)
	truncate_cto = frappe.db.sql(""" TRUNCATE `tabCompensatory Time Off Table` """)

	use_cto = frappe.db.sql(""" SELECT * FROM `tabCompensatory Time Off` WHERE `type` = 'Use' AND `workflow_state` = 'Approved' GROUP BY `name` ORDER BY `employee`, `use_date` ASC """, as_dict=1)
	for uc in use_cto:
		entries = []
		req_credits = uc.required_credits

		filed_cto = frappe.db.sql("""SELECT `name`, `credits_earned`, credits_used, balance, `date` FROM `tabCompensatory Time Off` 
		WHERE `type` = "File" AND `employee` = %(employee)s AND `docstatus` = 1 AND `workflow_state` = "Approved" AND `balance` > 0 GROUP BY `name` ORDER BY `date` ASC""",{
		"employee": uc.employee,
		"use_date": getdate(uc.use_date),
		}, as_dict=True)
		
		if filed_cto:
			for a in filed_cto:
				if req_credits > 0: 
					cred_used = 0.0
					if a.balance > 0:
						if flt(a.balance) >= flt(req_credits):
							remain_bal = a.balance - req_credits
							cred_used = req_credits
							req_credits = req_credits - cred_used
						else:
							remain_bal = 0.00
							cred_used = a.balance
							req_credits = req_credits - cred_used

						frappe.db.sql(""" UPDATE `tabCompensatory Time Off` SET `credits_used` = %s WHERE `name` = %s """,( flt(a.credits_used)+flt(cred_used), a.name))
						frappe.db.sql(""" UPDATE `tabCompensatory Time Off` SET `balance` = credits_earned-credits_used WHERE `name` = %s """,(a.name))
						row = {
							"cto_name": uc.name,
							"filed_cto": a.name,
							"date": a.date,
							"balance": a.balance,
							"credits_used": cred_used
						}
						entries.append(row);

		if entries:
			for ent in entries:
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

def add_total_amount_in_BE_and_RE(): #2019-09-02
	frappe.db.sql("""UPDATE `tabRecurring Entry` BE SET BE.total_amount=(SELECT SUM(BEE.`amount`) FROM `tabRecurring Entry Employees` BEE WHERE BEE.`parent`=BE.`name`) """)
	frappe.db.commit()

	frappe.db.sql("""UPDATE `tabBatch Entry` BE SET BE.total_amount=(SELECT SUM(BEE.`amount`) FROM `tabBatch Entry Employees` BEE WHERE BEE.`parent`=BE.`name`) """)
	frappe.db.commit()

def update_rate_format_in_movement(): #2019-10-15
	frappe.db.sql("""UPDATE `tabEmployee Movement` SET current_rate=FORMAT(current_rate, 2), current_minimum_take_home=FORMAT(current_minimum_take_home, 2) """)
	frappe.db.commit()

def rename_department():
	import frappe.model.rename_doc as rd

	frappe.db.sql("""UPDATE `tabDepartment` TD LEFT JOIN `tabCompany` TC ON TD.`company`=TC.`name` SET TD.`department_name`=TRIM(CONCAT(" - ", TC.abbr) FROM TD.`name`) """)

	dept_list = frappe.db.sql(""" SELECT TD.`name`, TD.`department_name`, TD.`company`, TC.`abbr` FROM `tabDepartment` TD LEFT JOIN `tabCompany` TC ON TD.`company`=TC.`name` WHERE TD.`company` IS NOT NULL AND is_root = 0 """, as_dict=1)
	for dept in dept_list:
		rd.rename_doc("Department", dept.name, cstr(dept.department_name)+" - "+cstr(dept.abbr), force=True)

def add_administrator_role():
	frappe.db.sql("""DELETE FROM `tabHas Role` WHERE `parent` = 'Administrator' AND parentfield = 'roles' AND parenttype = 'User' AND role = 'Administrator' """)
	frappe.db.commit()

	frappe.db.sql("""INSERT INTO `tabHas Role` (name, creation, modified, modified_by, owner, `docstatus`, parent, parentfield, parenttype, idx, role) 
		VALUES (LEFT(MD5(RAND()), 10), NOW(), NOW(), 'Administrator', 'Administrator', 0, 'Administrator', 'roles', 'User', 1, 'Administrator' ) """)

def add_fromdate_todate_cto():
	frappe.db.sql("""UPDATE `tabCompensatory Time Off` CTO SET is_previous=0, file_target_date=`date`, file_from_date=`date`, file_to_date=`date`, file_from_time=from_time, file_to_time=to_time WHERE type = 'File'; """)
	frappe.db.sql("""UPDATE `tabCompensatory Time Off` CTO SET is_previous=0, use_target_date=use_date, use_from_date=use_date, use_to_date=use_date, reason=use_reason, attachment=use_attachment WHERE type = 'Use'; """)
	frappe.db.sql("""UPDATE `tabCompensatory Time Off Table` CTT INNER JOIN `tabCompensatory Time Off` CTO ON CTT.`filed_cto`=CTO.`name` SET CTT.date=CTO.file_target_date; """)

def mark_processed_default_schedule():
	entry = {}
	csa_list = frappe.db.sql(""" SELECT CST.`target_date`, CST.`new_shift`, CSA.`employee` FROM `tabChange Schedule Application Table` CST INNER JOIN `tabChange Schedule Application` CSA ON CST.`parent`=CSA.`name` WHERE CSA.`workflow_state` = 'Approved' """, as_dict=1)
	for c in csa_list:
		if c.employee not in entry:
			entry[c.employee] = { 'dates': [] }
		if getdate(c.target_date) not in entry[c.employee]['dates']:
			entry[c.employee]['dates'].append(getdate(c.target_date))

	ws_list = frappe.db.sql(""" SELECT employee, target_date, work_shift FROM `tabWork Schedule` """, as_dict=1)
	for w in ws_list:
		if w.employee not in entry:
			entry[w.employee] = { 'dates': [] }
		if getdate(w.target_date) not in entry[w.employee]['dates']:
			entry[w.employee]['dates'].append(getdate(w.target_date))

	ar_list = frappe.db.sql(""" SELECT `name`, employee, target_date, work_shift, is_default_schedule FROM `tabAttendance Register` """, as_dict=1)
	for a in ar_list:
		if a.employee in entry:
			if (not a.is_default_schedule) and (getdate(a.target_date) not in entry[a.employee]['dates']):
				frappe.db.sql("""UPDATE `tabAttendance Register` SET is_default_schedule=1 WHERE `name` = %s """,(a.name))
	frappe.db.commit()

def update_min_take_home():
	frappe.db.sql("""UPDATE `tabEmployee` SET min_take_home=30, mth_percentage=1 WHERE is_active = 1; """)
	frappe.db.commit()

def update_date_contract_ended():
	update_list = {}
	movement_list = frappe.db.sql("""SELECT * FROM `tabEmployee Movement` WHERE movement_type = 'End of Contract' AND docstatus = 1 """, as_dict=1)
	for em in movement_list:
		if getdate(em.effective_on) <= getdate(nowdate()):
			if em.employee not in update_list:
				update_list[em.employee] = {
					"date_contract_ended": getdate(em.effective_on),
				}
			else:
				if getdate(em.effective_on) > update_list[em.employee]["date_contract_ended"]:
					update_list[em.employee]["date_contract_ended"] = getdate(em.effective_on)

			frappe.db.sql("""UPDATE `tabEmployee Movement` SET is_processed=1 WHERE `name` = %s """,(em.name))

	for up in update_list:
		frappe.db.sql("""UPDATE `tabEmployee` SET date_contract_ended=%s WHERE `name` = %s """,(getdate(update_list[up]["date_contract_ended"]), up))

def overtime_auto_break_update():
	print('Gathering Shifts.......')
	shitf_map = {}

	autobreaks = frappe.db.sql("""SELECT parent, break_mins, from_hrs, to_hrs FROM `tabOvertime Auto Break Table` WHERE `parenttype` = "Work Shift" """, as_dict=True)
	for ab in autobreaks:
		if ab.parent not in shitf_map:
			shitf_map[ab.parent] = {}

		if 'autobreaks' not in shitf_map[ab.parent]:
			shitf_map[ab.parent]['autobreaks'] = []

		shitf_map[ab.parent]['autobreaks'].append(ab)

	if shitf_map:
		updated_cnt = 0
		print('Gathering Overtime Applications........')
		Overtime_app_list = frappe.db.sql("""SELECT `name`, employee, target_date, break_mins, from_hrs, to_hrs, from_date, from_time, to_date, to_time  FROM  `tabOvertime Application`  WHERE break_hrs > 0 AND `creation` > "2020-01-01 00:00:00.000000" """, as_dict=1)
		goal_cnt = len(Overtime_app_list)
		print('Updating Overtime Applications........')
		for oa in Overtime_app_list:
			schedule = get_schedule(oa.employee, oa.target_date, oa.target_date)
			goal_cnt -= 1
			if schedule:
				if schedule[0]['work_shift'] in shitf_map:
					ws = schedule[0]['work_shift']
					from_date = str(oa.from_date) + ' ' + str(oa.from_time)
					to_date = str(oa.to_date) + ' ' + str(oa.to_time)
					total_hrs = datetimediff_hrs(from_date, to_date, "%Y-%m-%d %H:%M:%S")

					for ob in shitf_map[ws]['autobreaks']:
						if flt(ob['from_hrs']) <= flt(total_hrs) <= flt(ob['to_hrs']):
							frappe.db.sql("""UPDATE `tabOvertime Application` SET break_mins=%s, from_hrs=%s, to_hrs=%s WHERE `name` = %s """,(ob['break_mins'], ob['from_hrs'], ob['to_hrs'], oa.name))
							updated_cnt += 1
			print('Remaining: '+cstr(goal_cnt)+" "+"Updated:"+cstr(updated_cnt))
	print('Finished')

def update_ot_rates_holiday():
	holiday = 1
	ot_rates = frappe.db.sql("""SELECT `name`, is_restday, is_holiday, is_sp_holiday, is_db_holiday, is_sunday, is_saturday, is_excess, is_ndiff  FROM  `tabOvertime Rates`  WHERE (is_sp_holiday = 1 OR is_db_holiday = 1) AND is_holiday = 0 """, as_dict=1)
	for o in ot_rates: 
		frappe.db.set_value("Overtime Rates", o.name, "is_holiday", holiday)
		overtime_type = [o.is_restday, holiday, o.is_sp_holiday, o.is_db_holiday, o.is_sunday, o.is_saturday, o.is_excess, o.is_ndiff]
		overtime_type = ''.join(str(x) for x in overtime_type)
		existing_ot_code = frappe.db.sql("""SELECT `name` FROM  `tabOvertime Rates`  WHERE ot_code = %s """,overtime_type ,as_dict=1)
		if existing_ot_code:
			frappe.delete_doc("Overtime Rates", o.name)
		else:
			frappe.db.set_value("Overtime Rates", o.name, "ot_code", overtime_type)

def recompute_leavebalances():
	leaves = frappe.db.sql("""SELECT `name`, `total_leave_days`, `from_balance` FROM `tabLeave Application` 
		WHERE workflow_state IN ('Pending', 'Approval in Progress', 'Approved') AND `from_balance` IS NOT NULL AND `from_balance` != "" """, as_dict=1)

	shouldbe = {}
	for lv in leaves:
		if lv.from_balance not in shouldbe:
			shouldbe[lv.from_balance] = 0
		shouldbe[lv.from_balance] += lv.total_leave_days

	for s in shouldbe:
		leaves = frappe.db.sql(""" UPDATE `tabLeave Balance` SET used_credits=%(used_credits)s WHERE `name` = %(name)s """,{
			"used_credits": shouldbe[s],
			"name": s,
		})

def validate_loanpayments():
	payment_removed = []
	to_remove = []

	laps = frappe.db.sql("""SELECT LP.`name`, LP.`parent`, LA.`employee`, LP.payment_status, LP.payment_date, LA.beginning_balance, LP.payment_amount, LP.idx
		FROM `tabLoan Application Payments` LP INNER JOIN `tabLoan Application` LA ON LP.`parent`=LA.`name` WHERE LP.`payment_status` = 'Paid' """,as_dict=1)

	prs = frappe.db.sql("""SELECT employee, posting_date FROM `tabPayroll Register` PR """,as_dict=1)
	prs_dict = {}
	for p in prs:
		if p.employee not in prs_dict:
			prs_dict[p.employee] = []
		prs_dict[p.employee].append(getdate(p.posting_date))

	for l in laps:
		if getdate(l.payment_date) not in prs_dict[l.employee]:
			if (getdate(l.payment_date) == getdate('2020-03-14')):
				if flt(l.beginning_balance, 8) == flt(l.payment_amount, 8):
					if (l.idx != 1):
						frappe.db.sql("""UPDATE `tabLoan Application Payments` LP SET LP.payment_status='Unpaid', LP.payment_date=NULL WHERE LP.`name`=%s """,(l.name))
						frappe.db.sql("""UPDATE `tabLoan Application` SET unpaid_amount=unpaid_amount+%s, 
							paid_amount=paid_amount-%s WHERE `name`=%s """,(l.payment_amount, l.payment_amount, l.parent))
						payment_removed.append( "Employee: "+cstr(l.employee)+" Loan ID: "+cstr(l.parent)+" Payment Date: "+cstr(getdate(l.payment_date))  )
				else:
						frappe.db.sql("""UPDATE `tabLoan Application Payments` LP SET LP.payment_status='Unpaid', LP.payment_date=NULL WHERE LP.`name`=%s """,(l.name))
						frappe.db.sql("""UPDATE `tabLoan Application` SET unpaid_amount=unpaid_amount+%s, 
							paid_amount=paid_amount-%s WHERE `name`=%s """,(l.payment_amount, l.payment_amount, l.parent))
						payment_removed.append( "Employee: "+cstr(l.employee)+" Loan ID: "+cstr(l.parent)+" Payment Date: "+cstr(getdate(l.payment_date))  )
			else:
				if flt(l.beginning_balance, 8) == flt(l.payment_amount, 8):
					if (l.idx != 1):
						to_remove.append( "Employee: "+cstr(l.employee)+" Loan ID: "+cstr(l.parent)+" Payment Date: "+cstr(getdate(l.payment_date))  )
				else:
					to_remove.append( "Employee: "+cstr(l.employee)+" Loan ID: "+cstr(l.parent)+" Payment Date: "+cstr(getdate(l.payment_date))  )
	
	cnt = 0
	print( "Payments Removed: " )
	for pym in payment_removed:
		print(pym)
		cnt += 1
	print( "Total Payment Removed: "+cstr(cnt) )

	ct = 0
	print( "Payments To Remove: " )
	for trm in to_remove:
		print(trm)
		ct += 1
	print( "Total Payment To Remove: "+cstr(ct) )

def update_loans_payrollperiod():
	print('Gathering Loan Applications........')
	loan_update = frappe.db.sql("""SELECT LAP.`name` as "loan_name", P.`name` as "payroll_period" FROM `tabLoan Application Payments` LAP INNER JOIN `tabPayroll Period` P 
		on LAP.`payment_date` = P.`payroll_date` INNER JOIN `tabLoan Application` LA on LA.`name` = LAP.`parent` 
		WHERE LAP.`payment_status` = 'Paid' AND P.`company` = LA.`company`""", as_dict=True )
	updated_loan = 0
	loan_count = len(loan_update)
	for l in loan_update:
		loan_count -= 1
		updated_loan +=1
		frappe.db.sql("""UPDATE `tabLoan Application Payments` SET  payroll_period = %s WHERE `name` = %s   """,(l.payroll_period, l.loan_name))
		print('Remaining: '+cstr(loan_count)+" "+"Updated:"+cstr(updated_loan))
	print('Finished')

def convert_ctocreds():
	frappe.db.sql(""" UPDATE `tabCompensatory Time Off` SET old_total_credits_earned = total_credits_earned WHERE `type` = 'Use' """)
	ctos = frappe.db.sql(""" SELECT * FROM `tabCompensatory Time Off` WHERE docstatus != 2 """, as_dict=1)
	fctotabs = frappe.db.sql(""" SELECT CT.`name`, CT.`filed_cto`, CT.`credits_used`, CT.`balance`, CT.`forfeited_balance`, C.`total_hours`, C.`credits_earned` 
		FROM `tabCompensatory Time Off Table` CT INNER JOIN `tabCompensatory Time Off` C ON CT.`filed_cto`=C.`name` WHERE C.type = 'File' """, as_dict=1)

	for ct in fctotabs:
		if ct.total_hours:
			nce, ncu, nb, nfb = 0, 0, 0, 0
			nce = ct.total_hours
			ncu = (((ct.credits_used *100) / ct.credits_earned) / 100) * ct.total_hours
			nb = (((ct.balance *100) / ct.credits_earned) / 100) * ct.total_hours
			nfb = (((ct.forfeited_balance *100) / ct.credits_earned) / 100) * ct.total_hours
			frappe.db.sql(""" UPDATE `tabCompensatory Time Off Table` SET forfeited_balance=%s, credits_used=%s, balance=%s WHERE `name` = %s """,(nfb, ncu, nb, ct.name))

	for c in ctos:
		if c.type == 'File' and c.total_hours and c.credits_earned:
			nce, ncu, nb = 0, 0, 0
			nce = c.total_hours
			ncu = (((c.credits_used *100) / c.credits_earned) / 100) * c.total_hours
			nb = (((c.balance *100) / c.credits_earned) / 100) * c.total_hours
			frappe.db.sql(""" UPDATE `tabCompensatory Time Off` SET credits_earned=total_hours, credits_used=%s, balance=%s WHERE `name` = %s """,(ncu, nb, c.name))

	ectotabs = frappe.db.sql(""" SELECT CT.`name`, CT.filed_cto, CT.credits_used, CT.balance, CT.forfeited_balance, CT.parent
		FROM `tabCompensatory Time Off Table` CT INNER JOIN `tabCompensatory Time Off` C ON CT.`parent`=C.`name` """, as_dict=1)

	edic = {}
	for e in ectotabs:
		if e.parent not in edic:
			edic[e.parent] = 0
		edic[e.parent] += e.balance

	for ec in ctos:
		if ec.type == 'Use':
			if ec.name in edic:
				frappe.db.sql(""" UPDATE `tabCompensatory Time Off` SET total_credits_earned=%s, required_credits=use_total_hours WHERE `name` = %s """,(flt(edic[ec.name]), ec.name))
			else:
				frappe.db.sql(""" UPDATE `tabCompensatory Time Off` SET total_credits_earned=use_total_hours, required_credits=use_total_hours WHERE `name` = %s """,(ec.name))

def targetdate_in_utapp():
	frappe.db.sql(""" UPDATE `tabUndertime Application` SET target_date=from_date, to_date=from_date""")

def update_payroll_date():
	date = "2020-06-15"
	frappe.db.sql(""" UPDATE `tabPayroll Period` SET `payroll_date`= %s WHERE `name` = "May21 Jun05 - JR&R2020" """,(date))

def approved_on_to_datetime():
	frappe.db.sql(""" UPDATE `tabChange Schedule Application` SET approved_on=modified WHERE docstatus = 1 AND workflow_state = 'Approved'""")
	frappe.db.sql(""" UPDATE `tabDTR Problem Application` SET approved_on=modified WHERE docstatus = 1 AND workflow_state = 'Approved'""")

def convert_leave_balacnce_to_lb_entry():
	current_employees = []
	employee_list = frappe.db.sql("""SELECT `name` FROM `tabEmployee` """, as_dict=1)
	for el in employee_list:
		current_employees.append(el.name)

	included_old = []
	leave_balance = frappe.db.sql("""SELECT * FROM `tabLeave Balance` WHERE `credits` > 0 """, as_dict=1)
	for d in leave_balance:
		if d.employee in current_employees:
			old_from_balance = d.name
			if old_from_balance and old_from_balance not in included_old:
				included_old.append(old_from_balance)

			full_name = None
			get_full_name = frappe.db.get_value("Employee", d['employee'], ["full_name"])
			if get_full_name:
				full_name = get_full_name

			company = None
			get_company = frappe.db.get_value("Employee", d['employee'], ["company"])
			if get_company:
				company = get_company

			lb = frappe.new_doc("LB Entry")
			lb.update({
				"employee": d.employee,
				"employee_name": full_name,
				"posting_date": nowdate(),
				"company": company,
				"leave_type": d.leave_type,
				"balance_type": 'Add',
				"created_from": 'Execute Script',
				"from_date": d.from_date,
				"to_date": d.to_date,
				"credits": d.credits,
				"deduct_credits_to": None
			})
			lb.flags.ignore_permissions = True
			lb.flags.ignore_validate = True
			lb.insert()
			new_from_balance = lb.name
			if old_from_balance in included_old:
				frappe.db.sql("""UPDATE `tabLeave Application` SET from_balance=%s, old_from_balance=%s WHERE from_balance = %s AND leave_type = %s """,(new_from_balance, old_from_balance, old_from_balance, d.leave_type))

	leave_apps = frappe.db.sql("""SELECT * FROM `tabLeave Application` WHERE `docstatus` = 1 AND `workflow_state` = 'Approved' """, as_dict=1)
	for ap in leave_apps:
		if ap.total_leave_days and ap.employee in current_employees:
			
			full_name = None
			get_fullname = frappe.db.get_value("Employee", d['employee'], ["full_name"])
			if get_fullname:
				full_name = get_fullname
				
			company = None
			get_company_name = frappe.db.get_value("Employee", d['employee'], ["company"])
			if get_company_name:
				company = get_company_name

			if ap.company:
				company = ap.company

			alb = frappe.new_doc("LB Entry")
			alb.update({
				"employee": ap.employee,
				"employee_name": ap.full_name,
				"posting_date": ap.posting_date,
				"company": company,
				"leave_type": ap.leave_type,
				"balance_type": 'Less',
				"created_from": 'Leave Application',
				"linked_document": ap.name,
				"from_date": ap.from_date,
				"to_date": ap.to_date,
				"credits": ap.total_leave_days,
				"deduct_credits_to": ap.leave_type,
			})
			alb.flags.ignore_permissions = True
			alb.flags.ignore_validate = True
			alb.insert()
			frappe.db.sql("""UPDATE `tabLeave Application` SET linked_lb_entry=%s WHERE `name` = %s """,(alb.name, ap.name))

def convert_leave_balacnce_to_lb_entry_balance_only():
	current_employees = []
	employee_list = frappe.db.sql("""SELECT `name` FROM `tabEmployee` """, as_dict=1)
	for el in employee_list:
		current_employees.append(el.name)

	included_old = []
	leave_balance = frappe.db.sql("""SELECT * FROM `tabLeave Balance` WHERE `credits` > 0 """, as_dict=1)
	for d in leave_balance:
		if d.employee in current_employees:
			old_from_balance = d.name
			if old_from_balance and old_from_balance not in included_old:
				included_old.append(old_from_balance)

			full_name = None
			get_full_name = frappe.db.get_value("Employee", d['employee'], ["full_name"])
			if get_full_name:
				full_name = get_full_name

			company = None
			get_company = frappe.db.get_value("Employee", d['employee'], ["company"])
			if get_company:
				company = get_company

			lb = frappe.new_doc("LB Entry")
			lb.update({
				"employee": d.employee,
				"employee_name": full_name,
				"posting_date": nowdate(),
				"company": company,
				"leave_type": d.leave_type,
				"balance_type": 'Add',
				"created_from": 'Execute Script',
				"from_date": d.from_date,
				"to_date": d.to_date,
				"credits": d.credits - d.used_credits,
				"deduct_credits_to": None
			})
			lb.flags.ignore_permissions = True
			lb.flags.ignore_validate = True
			lb.insert()
			new_from_balance = lb.name
			if old_from_balance in included_old:
				frappe.db.sql("""UPDATE `tabLeave Application` SET old_from_balance=%s, from_balance=%s WHERE from_balance = %s AND leave_type = %s """,(old_from_balance, new_from_balance, old_from_balance, d.leave_type))
	frappe.db.sql("""UPDATE `tabLeave Application` SET without_lbentry=1 """)

def move_my_payslip_leave_to_my_profile():
	frappe.db.sql("""UPDATE `tabDocType` SET module = 'My Profile' WHERE `name`= 'My Payslip Leave'""")

def remove_lbentries_with_no_leave_application():
	frappe.db.sql("""DELETE FROM `tabLB Entry` WHERE `balance_type` = 'Less' AND created_from = 'Leave Application' AND `name` NOT IN (SELECT `linked_lb_entry` FROM `tabLeave Application` WHERE `linked_lb_entry` IS NOT NULL) """)

def add_month_in_payroll_period():
	period_list = frappe.db.sql(""" SELECT `name`, `from_date`, `to_date` FROM `tabPayroll Period` WHERE `payroll_month` IS NULL """, as_dict=1)
	for period in period_list:
		payroll_month = calendar.month_name[list(calendar.month_abbr).index(period.name[:3])]
		frappe.db.sql(""" UPDATE `tabPayroll Period` SET `payroll_month`=%s WHERE `name` = %s """,( payroll_month, period.name ) )
		frappe.db.commit()

def fix_lbentry_fromdate():
	#frappe.db.sql(""" UPDATE `tabLB Entry` SET from_date=DATE(creation) """)
	#frappe.db.sql(""" DELETE FROM `tabLB Entry` wHERE created_from = 'Execute Script' """)
	frappe.db.sql(""" UPDATE `tabLB Entry` SET from_date=DATE(creation) WHERE created_from IN ('LB Scheduler - Carry Over', 'LB Scheduler') """)
	frappe.db.sql(""" UPDATE `tabLB Entry` LB JOIN `tabLeave Application` LA ON LB.`linked_document`=LA.`name` SET LB.`from_date`=LA.`from_date` WHERE LB.`created_from` = 'Leave Application' """)
	#frappe.db.sql(""" DELETE FROM `tabLB Entry` wHERE created_from = 'Execute Script' """)

	lbentries = frappe.db.sql(""" SELECT `name`, `employee`, `from_date`, `to_date`, `leave_type` FROM `tabLB Entry` WHERE created_from = 'Execute Script' """, as_dict=1)	
	for lb in lbentries:
		oldlb = frappe.db.sql(""" SELECT `name`, `from_date`, `to_date` FROM `tabLeave Balance` WHERE `employee`=%s AND `to_date`=%s AND `leave_type`=%s """,(lb.employee, lb.to_date, lb.leave_type), as_dict=1)
		if oldlb:
			frappe.db.sql(""" UPDATE `tabLB Entry` SET from_date=%s WHERE `employee`=%s AND `to_date`=%s AND `leave_type`=%s AND created_from = 'Execute Script' """,(oldlb[0].from_date, lb.employee, lb.to_date, lb.leave_type), as_dict=1)

def fix_lbentry_fromdate_partial():
	#frappe.db.sql(""" UPDATE `tabLB Entry` SET from_date=DATE(creation) """)
	#frappe.db.sql(""" DELETE FROM `tabLB Entry` wHERE created_from = 'Execute Script' """)
	#frappe.db.sql(""" UPDATE `tabLB Entry` SET from_date=DATE(creation) WHERE created_from IN ('LB Scheduler - Carry Over', 'LB Scheduler') """)
	frappe.db.sql(""" UPDATE `tabLB Entry` LB JOIN `tabLeave Application` LA ON LB.`linked_document`=LA.`name` SET LB.`from_date`=LA.`from_date` WHERE LB.`created_from` = 'Leave Application' """)
	#frappe.db.sql(""" DELETE FROM `tabLB Entry` wHERE created_from = 'Execute Script' """)

	#lbentries = frappe.db.sql(""" SELECT `name`, `employee`, `from_date`, `to_date`, `leave_type` FROM `tabLB Entry` WHERE created_from = 'Execute Script' """, as_dict=1)	
	#for lb in lbentries:
	#	oldlb = frappe.db.sql(""" SELECT `name`, `from_date`, `to_date` FROM `tabLeave Balance` WHERE `employee`=%s AND `to_date`=%s AND `leave_type`=%s """,(lb.employee, lb.to_date, lb.leave_type), as_dict=1)
	#	if oldlb:
	#		frappe.db.sql(""" UPDATE `tabLB Entry` SET from_date=%s WHERE `employee`=%s AND `to_date`=%s AND `leave_type`=%s AND created_from = 'Execute Script' """,(oldlb[0].from_date, lb.employee, lb.to_date, lb.leave_type), as_dict=1)

def cto_multi_file():
	old_ctos = frappe.db.sql(""" SELECT * FROM `tabCompensatory Time Off` """, as_dict=1)

	if old_ctos:
		for old in old_ctos:
			from_date = None
			to_date = None
			from_time = None
			to_time = None
			total_credits_earned = None
			total_required_credits = None
			total_credits_used = None
			total_break_hours = None
			total_hours = None
			total_balance = None

			if old.type == "File":
				if old.file_target_date and old.file_from_date and old.file_to_date and old.file_from_time and old.file_to_time:
					cto_table = frappe.new_doc("Compensatory Time Off Targets")
					cto_table.update({
						'parentfield': 'cto_targets',
						'parenttype': 'Compensatory Time Off',
						'parent': old.name,
						'target_date': old.file_target_date,
						'is_previous': old.is_previous,
						'from_date': old.file_from_date,
						'to_date': old.file_to_date,
						'from_time': old.file_from_time,
						'to_time': old.file_to_time,
						'break_hours': old.break_hours,
						'cto_hours': old.total_hours,
						'credits_earned': old.credits_earned,
						'credits_used': old.credits_used,
						'balance': old.balance,
						'actual_in': old.file_actual_in,
						'actual_out': old.file_actual_out,
						#'docstatus': old.docstatus,
					})
					cto_table.flags.ignore_permissions = True
					cto_table.flags.ignore_validate = True
					cto_table.insert()
					from_date = old.file_from_date
					to_date = old.file_to_date
					from_time = old.file_from_time
					to_time = old.file_to_time
					total_credits_earned = old.credits_earned
					total_required_credits = None
					total_credits_used = old.credits_used
					total_break_hours = old.break_hours
					total_hours = old.total_hours
					total_balance = old.balance

			if old.type == "Use":
				if  old.use_target_date and old.use_from_date and old.use_to_date and old.use_fromtime and old.use_totime:
					cto_table = frappe.new_doc("Compensatory Time Off Targets")
					cto_table.update({
						'parentfield': 'cto_targets',
						'parenttype': 'Compensatory Time Off',
						'parent': old.name,
						'target_date': old.use_target_date,
						'is_previous': old.is_previous,
						'from_date': old.use_from_date,
						'to_date': old.use_to_date,
						'from_time': old.use_fromtime,
						'to_time': old.use_totime,
						'filed_cto': old.filed_cto,
						'break_hours': old.use_break_hours,
						'cto_hours': old.use_total_hours,
						'credits_earned': old.total_credits_earned,
						'required_credits': old.required_credits,
						#'docstatus': old.docstatus,
					})
					cto_table.flags.ignore_permissions = True
					cto_table.flags.ignore_validate = True
					cto_table.insert()
					from_date = old.use_from_date
					to_date = old.use_to_date
					from_time = old.use_fromtime
					to_time = old.use_totime
					total_credits_earned = old.total_credits_earned
					total_required_credits = old.required_credits
					total_credits_used = old.credits_used
					total_break_hours = old.use_break_hours
					total_hours = old.use_total_hours
					total_balance = old.balance

			if from_date:
				from_date = getdate(from_date)
			if to_date:
				to_date = getdate(to_date)
				
			frappe.db.sql(""" UPDATE `tabCompensatory Time Off` SET 
				`from_date` = %(from_date)s,
				`to_date` = %(to_date)s,
				`from_time` = %(from_time)s,
				`to_time` = %(to_time)s,
				`total_credits_earned`= %(total_credits_earned)s,
				`total_required_credits`= %(total_required_credits)s,
				`total_credits_used`= %(total_credits_used)s,
				`total_break_hours`= %(total_break_hours)s,
				`total_hours`= %(total_hours)s,
				`total_balance`= %(total_balance)s WHERE `name` = %(name)s """,{
				'from_date': from_date,
				'to_date': to_date,
				'from_time': from_time,
				'to_time': to_time,
				'total_credits_earned': total_credits_earned,
				'total_required_credits': total_required_credits,
				'total_credits_used': total_credits_used,
				'total_break_hours': total_break_hours,
				'total_hours': total_hours,
				'total_balance': total_balance,
				'name': old.name,
			}, as_dict=True)

		frappe.db.sql(""" UPDATE `tabCompensatory Time Off Targets` CTT INNER JOIN `tabCompensatory Time Off` CTO ON CTT.`parent`=CTO.`name`
			SET CTT.docstatus = CTO.docstatus WHERE CTT.docstatus != CTO.docstatus """, as_dict=True)

def add_approved_on_and_by():
	application_type_list = ["Official Business Application", "Leave Application", "Overtime Application", "Change Schedule Application", "Excuse Tardiness Application", "Undertime Application", "Compensatory Time Off", "DTR Problem Application"]
	for app in application_type_list:
		table = "`tab"+app+"`"
		table = str(table)
		frappe.db.sql(""" UPDATE """+table+""" SET approved_on = modified, approved_by = modified_by WHERE docstatus = 1 AND (approved_on IS NULL OR approved_on = '') AND (approved_by IS NULL OR approved_by = '') """)

def update_failed_approved_docstatus():
	application_type_list = ["Official Business Application", "Leave Application", "Overtime Application", "Change Schedule Application", "Excuse Tardiness Application", "Undertime Application", "Compensatory Time Off", "DTR Problem Application"]
	for app in application_type_list:
		table = "`tab"+app+"`"
		table = str(table)

		frappe.db.sql(""" UPDATE """+table+""" SET docstatus = 1 WHERE docstatus = 0 AND workflow_state = 'Approved' """)

def update_leave_date():
	leave_list = ["LAP00000618", "LAP00000756", "LAP00001698", "LAP00001958", "LAP00002759", "LAP00002760"]
	leave_app = frappe.db.sql(""" SELECT * FROM `tabLeave Application` WHERE `name` in %s """,(leave_list), as_dict=1)

	for l in leave_app:
		frappe.db.sql("""DELETE FROM `tabLB Entry` WHERE created_from = "Leave Application" AND linked_document = %s""",(l.name))
		l.linked_lb_entry = ""
		total_balance = 0
		l.set('leave_application_table', [])
		if not l.from_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> No From Date").format(l.name))

		if not l.to_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> No To Date").format(l.name))
		
		if l.from_date > l.to_date:
			frappe.throw(_("<b>Leave Application: {0}</b><hr> To From Date Should be Greater than To").format(l.name))
			
		else:
			entries = [];
			dates = [];
			leave_application_table = [];
			start = datetime.datetime.strptime(l.from_date, '%Y-%m-%d')
			end = datetime.datetime.strptime(l.to_date, '%Y-%m-%d')
			step = datetime.timedelta(days=1)
		
			while start <= end:
			    dates.append(start.date());
			    start += step
		    
			for i in dates:
				holiday_tag  = 0
				location = frappe.get_value("Employee", l.employee, "location")
			
				holiday = frappe.db.sql("""SELECT `name`, location FROM `tabHoliday` WHERE holiday_date = %s 
					AND company = %s """, (getdate(target_date), l.company), as_dict=True)
			
				if holiday:
					if holiday[0].location:
						if holiday[0].location == location:
							holiday_tag = 1	
					else:
						holiday_tag = 1
				info = {
			        "leave_date": i,
			        "is_holiday": holiday_tag,
			        "is_halfday": 0,
			        "is_excluded": 0
			    }

				leave_application_table.append(info);
		
			entries = sorted(list(leave_application_table), 
				key=lambda k: k['leave_date'])		    
			l.set('leave_application_table', [])
			
			for d in entries:
				row = l.append('leave_application_table', {})
				row.update(d)
			
		total_leave_days = 0
		inc_holidays, leave_code = frappe.get_value("Leave Type", l.leave_type, ["include_holidays", "leave_code"])

		for d in l.get('leave_application_table'):
			add_days = 1

			if d.is_half_day == 1:
				add_days = 0.5			
			
			if d.is_holiday == 1:
				if inc_holidays == 1:
					add_days = 1
				else:
					add_days = 0
			
			if d.is_second_half == 1:
				d.is_half_day = 1
				add_days = 0.5

			if getdate(d.leave_date).weekday() == 5:
				lvbal_saturday = frappe.get_value("Employee", l.employee, "lvbal_saturday")
				if lvbal_saturday > 0:
					add_days = flt(lvbal_saturday, 8)

			if d.is_excluded == 1:
				add_days = 0
				
			total_leave_days += add_days

			if leave_code == "BL":
				schedule = get_schedule(l.employee, d.leave_date, d.leave_date)
				if schedule:
					shifts = frappe.db.sql("""SELECT DISTINCT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(schedule[0]['work_shift']), as_dict=True)
					if shifts:
						if shifts[0].is_restday > 0:
							total_leave_days = 0
				holiday_tag  = 0
				location = frappe.get_value("Employee", l.employee, "location")
			
				holiday = frappe.db.sql("""SELECT `name`, location FROM `tabHoliday` WHERE holiday_date = %s 
					AND company = %s """, (getdate(target_date), l.company), as_dict=True)
			
				if holiday:
					if holiday[0].location:
						if holiday[0].location == location:
							holiday_tag = 1	
					else:
						holiday_tag = 1
				holiday_leave = holiday_tag
				if holiday_leave:
					total_leave_days = 0

		l.total_leave_days = total_leave_days
		valid_entry = {}
		less_entry = {}
		from_balance = ""
		add, less, total_balance = 0, 0, 0
		min_date = None
		deduct_to = frappe.get_value("Leave Type", l.leave_type, "deduct_to")
		if not deduct_to:
			deduct_to = l.leave_type
		
		lb_entries = frappe.db.sql(""" SELECT * FROM `tabLB Entry` WHERE `employee` = %s AND 
			(`leave_type` = %s OR `deduct_credits_to` = %s) AND `company` = %s ORDER BY `from_date` 
			ASC """, (l.employee, l.leave_type, l.leave_type, l.company), as_dict=1)

		for d in lb_entries:
			if d.balance_type == "Add":
				if l.leave_type == d.leave_type:
					if d.name not in valid_entry:
						valid_entry[d.name] = {
							"credits": d.credits,
							"from": getdate(d.from_date),
							"to": getdate(d.to_date),
							"used": 0,
						}
			else:
				if d.deduct_credits_to == l.leave_type:
					if d.name not in less_entry:
						less_entry[d.name] = {
							"used": 0,
							"credits": d.credits,
							"from": getdate(d.from_date),
							"to": getdate(d.to_date),
						}

		have_lbentry = 0
		for vl in valid_entry:
			for le in less_entry:
				to_less = 0
				if valid_entry[vl]['credits'] > 0 and not less_entry[le]['used']:
					if ( valid_entry[vl]['from'] <= less_entry[le]['from'] <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= less_entry[le]['to'] <= valid_entry[vl]['to'] ):
						if less_entry[le]['credits'] > valid_entry[vl]['credits']:
							to_less += valid_entry[vl]['credits']
							less_entry[le]['credits'] -= valid_entry[vl]['credits']
						else:
							to_less += less_entry[le]['credits']
							less_entry[le]['used'] = 1
					valid_entry[vl]['credits'] -= to_less
			if getdate(valid_entry[vl]['from']) <= getdate(l.from_date) and getdate(valid_entry[vl]['to']) >= getdate(l.to_date) and valid_entry[vl]['credits'] > 0:
				if total_balance < l.total_leave_days:
					from_balance += cstr(vl)
				total_balance += valid_entry[vl]['credits']
				valid_entry[vl]['used'] = 1
				have_lbentry = 1
				
		if have_lbentry == 1:
			for vl in valid_entry:
				if valid_entry[vl]['used'] == 0 and valid_entry[vl]['credits'] > 0:
					if ( valid_entry[vl]['from'] <= getdate(l.from_date) <= valid_entry[vl]['to'] ) or ( valid_entry[vl]['from'] <= getdate(l.to_date) <= valid_entry[vl]['to'] )\
					or ( getdate(l.from_date) <= valid_entry[vl]['from'] <= getdate(l.to_date) ) or ( getdate(l.from_date) <= valid_entry[vl]['to'] <= getdate(l.to_date) ):
						if total_balance < l.total_leave_days:
							from_balance += cstr(vl)
						total_balance += valid_entry[vl]['credits']
						valid_entry[vl]['used'] = 1

		l.from_balance = from_balance
		if total_balance <= 0:
			total_balance = 0
		l.leave_balance = total_balance
		frappe.db.sql("""UPDATE `tabLeave Application` SET from_balance=%s, leave_balance = %s, leave_application_table = %s,  
			WHERE `name` = %s """,(l.from_balance, l.leave_balance, l.leave_application_table, l.name))

		#create lb entry
		if l.workflow_state == 'Approved' and not l.linked_lb_entry:
			deduct_to = frappe.get_value("Leave Type", l.leave_type, "deduct_to")
			if not deduct_to:
				deduct_to = l.leave_type

			lb = frappe.new_doc("LB Entry")
			lb.update({
				"employee": l.employee,
				"employee_name": l.full_name,
				"posting_date": nowdate(),
				"company": l.company,
				"leave_type": l.leave_type,
				"balance_type": 'Less',
				"created_from": 'Leave Application',
				"linked_document": l.name,
				"from_date": l.from_date,
				"to_date": l.to_date,
				"credits": l.total_leave_days,
				"deduct_credits_to": deduct_to,
			})
			lb.flags.ignore_permissions = True
			lb.insert()
			l.db_set("linked_lb_entry", lb.name)

def update_old_loan_application_frequency_method():
	frappe.db.sql("""UPDATE `tabLoan Application` SET first_frequency=0, second_frequency=0, third_frequency=0, fourth_fifth_frequency=0 """)
	frappe.db.sql("""UPDATE `tabLoan Application` LA INNER JOIN `tabEmployee` TE ON LA.`employee`=TE.`name` SET LA.payroll_schedule=TE.payroll_schedule WHERE LA.payroll_schedule IS NULL """)
	frappe.db.sql("""UPDATE `tabLoan Application` SET first_frequency=1 WHERE freq_method ='Automatic' AND payment_frequency='1st' """)
	frappe.db.sql("""UPDATE `tabLoan Application` SET second_frequency=1 WHERE freq_method ='Automatic' AND payment_frequency='2nd' """)
	frappe.db.sql("""UPDATE `tabLoan Application` SET second_frequency=1, fourth_fifth_frequency=1 WHERE freq_method ='Automatic' AND payment_frequency='Both' AND payroll_schedule = 'Weekly' """)
	frappe.db.sql("""UPDATE `tabLoan Application` SET second_frequency=1, first_frequency=1 WHERE freq_method ='Automatic' AND payment_frequency='Both' AND payroll_schedule = 'Semi-Monthly' """)

def worksuspension_to_datetime():
	frappe.db.sql("""UPDATE `tabWork Suspension` SET to_time=suspension_end, from_time=suspension_start """)

def set_employee_gsis_setup():
	frappe.db.sql("""UPDATE `tabEmployee` SET gsis_mode='None', gsis_frequency='1st' WHERE gsis_mode IS NULL and gsis_frequency IS NULL """)

def set_movement_processed():
	frappe.db.sql("""UPDATE `tabEmployee Movement` SET is_processed=1, date_processed=effective_on WHERE effective_on<=%s AND is_processed!=1 AND docstatus=1 ORDER BY `modified` ASC """,(today()),as_dict=True)

def update_user_perm_period_group():
	employee = frappe.db.sql(""" SELECT `name`, `user_id`, `period_group` FROM `tabEmployee` """, as_dict=1)
	for emp in employee:
		if emp.period_group and emp.user_id:
			user_perm = frappe.db.sql(""" SELECT `for_value` FROM `tabUser Permission` WHERE `user` = %s AND `allow` = "Period Group" """,(emp.user_id) , as_dict=1)
			if user_perm != emp.period_group:
				frappe.db.sql("""DELETE FROM `tabUser Permission` WHERE `user` = %s AND allow = "Period Group" """,(emp.user_id),as_dict=True)
				frappe.permissions.add_user_permission("Period Group", emp.period_group, emp.user_id)
		else:
			frappe.db.sql("""DELETE FROM `tabUser Permission` WHERE `user` = %s AND allow = "Period Group" """,(emp.user_id),as_dict=True)

def workschedule_set_employeename():
	frappe.db.sql("""UPDATE `tabWork Schedule` WS INNER JOIN `tabEmployee` TE ON WS.`employee`=TE.`name` SET WS.`employee_name`=TE.`full_name` WHERE WS.`employee_name` IS NULL """)

def leave_days_before_filing_setup():
	leave_types = frappe.get_all('Leave Type')
	for lt in leave_types:
		doc = frappe.get_doc('Leave Type', lt.name)
		if doc.filing_days and not doc.days_before_filing:
			row = {
				"days_before_filing": doc.filing_days,
			}
			doc.append('days_before_filing', row)
		doc.save()

def reset_administrator_roles():
	import string
	import random

	roles = ["Administrator", "System Manager", "Accounts Manager", "Accounts User", "All", "Blogger", "Guest", "Knowledge Base Contributor", "Knowledge Base Editor", 
		"Maintenance Manager", "Maintenance User", "Newsletter Manager", "Purchase Manager", "Purchase Master Manager", "Purchase User", "Report Manager", 
		"Sales Master Manager", "Sales User", "Website Manager", "HR Manager", "Time Keeping Manager", "Payroll Manager", "Rank and File", "Leave Approver", 
		"Overtime Approver", "Official Business Approver", "Employee", "Change Schedule Approver", "DTR Problem Approver", "Excused Tardiness Approver", "Undertime Approver", 
		"Change Request Approver", "Station Supervisor", "Officer", "Manager", "HR Admin", "HR User", "Compensatory Time Off Approver", "Admin Approver", "PA CA Approver", 
		"HR Comp Ben", "Public Post", "Sales Manager", "Timekeeper Approver", "Timelogs Application Approver", "Approver", "Query Report Manager"]

	idx = 0

	for role in roles:
		N = 10
		res = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))
		res = res.lower()
		if not frappe.get_all('Has Role', fields={'name', 'role'}, filters={'name': res, 'role': role}):
			idx += 1
			frappe.db.sql(""" INSERT INTO `tabHas Role`
				(`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `parent`, `parentfield`, `parenttype`, `idx`, `role`) 
				VALUES 
				(%s, NOW(), NOW(), 'Administrator', 'Administrator', 0, 'Administrator', 'roles', 'User', %s, %s) """,( str(res), idx, role ),as_dict=1)

def add_dtrp_targetdate():
	frappe.db.sql("""UPDATE `tabDTR Problem Application` SET dtr_date=target_date """)
	frappe.db.sql("""UPDATE `tabDTR Problem Application` SET target_date=DATE_SUB(dtr_date, INTERVAL 1 DAY) WHERE is_previous = 1 """)

#Patch v1.91.00
def add_payrollprocesslogs_to_payslipgenerationlogs():
	payroll_process_logs = frappe.get_all('Payroll Process Logs', fields=['*'])
	for ppl in payroll_process_logs:
		payslip_generation = frappe.new_doc("Payslip Generation Logs")
		payslip_generation.update(ppl)
		payslip_generation.insert(ignore_permissions=True)

def update_loans_status():
	loans = frappe.get_all('Loan Application', fields=['name'])
	for loan in loans:
		doc = frappe.get_doc("Loan Application", loan.name)
		doc.run_method("update_loan_status")