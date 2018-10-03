from __future__ import unicode_literals
import frappe, datetime, math
from frappe.utils import cint, cstr, flt, nowdate, add_days, getdate, fmt_money, get_datetime, add_to_date
from frappe import _

def get_attendance(entry, leaves, holidays, obs, ots, uts, ext):
	if obs:
		for ob in obs:
			if ob['target_date'] == entry['target_date']:
				entry['linked_ob'] = ob.name
				entry['is_ob'] = 1

				entry['ob_status'] = 1
				entry["is_absent"] = 0
				entry['is_lwop'] = 0

				ob_in = get_datetime( str(entry.get('target_date'))+" "+ str(ob.from_time) )
				if not entry['ob_in']:
					entry['ob_in'] = ob_in
				elif entry['ob_in'] and ob_in < entry['ob_in']:
					entry['ob_in'] = ob_in

				ob_out = get_datetime( str(entry.get('target_date'))+" "+ str(ob.to_time) )
				if not entry['ob_out']:
					entry['ob_out'] = ob_out
				elif entry['ob_out'] and ob_out > entry['ob_out']:
					entry['ob_out'] = ob_out

				if entry['ob_out']  < entry['ob_in']:
					ob_date = add_days(entry.get('target_date'), 1)
					entry['ob_out'] = get_datetime( str(ob_date)+" "+ str(ob.to_time) )
		
	#if getdate(entry['target_date']) and getdate("2018-08-02"):
	#	frappe.throw(_(entry['ob_in']))


	if ots:
		for ot in ots:
			if getdate(ot['target_date']) == entry['target_date']:
				entry['overtime'] += ot.total_hrs * 60 * 60
				entry['linked_ot'] = ot.name
				entry['ot_in'] = get_datetime( str(ot.from_date) +" "+ str(ot.from_time) )
				entry['ot_out'] = get_datetime( str(ot.to_date) +" "+ str(ot.to_time) )

	if uts:
		for ut in uts:
			if ut['from_date'] == entry['target_date']:
				entry['ut_from'] = ut.from_time
				entry['ut_to'] = ut.to_time
				entry['linked_ut'] = ut.name

	if ext:
		for et in ext:
			if et['date'] == entry['target_date']:
				entry['ex_tardiness'] = 1

	if holidays:
		dbh = 0
		for h in holidays:
			if h['holiday_date'] == entry['target_date']:
				dbh += 1
				entry["is_absent"] = 0
				entry['is_lwop'] = 0
				entry["undertime"] = 0
				entry["late"] = 0
				entry['holiday_name'] = h['holiday_name']
				entry['is_holiday'] = 1
				if h['is_special'] == 1:
					entry['is_sp_holiday'] = 1

				#if not entry['card_in'] or not entry['card_out']:
				#	entry['work'] = entry.get('work_hours') * 60 * 60
		if dbh >= 2:
			entry['is_db_holiday'] = 1

	#leaves	
	for l in leaves:
		if l['leave_date'] == entry['target_date']:
			if l['is_excluded'] != 1:
				entry['leave_name'] = l.leave_type
				entry['linked_leave'] = l.name
				entry["lv_status"] = 1
				if not entry['card_in'] or not entry['card_out']:
					entry['work'] = (entry.get('work_hours') * 60) * 60

				if l.is_lwop == 1:
					entry['is_lwop'] = 1
				
				if l.is_half_day:
					entry["lv_status"] = 2

				if l.is_second_half:
					entry["lv_status"] = 3

	get_late(entry)
	get_undertime(entry)
	get_overtime(entry)
	get_ndiff(entry)
	get_absent(entry)
	get_work(entry)
	get_final_processing(entry)
	get_tags(entry)

def get_work(entry):
	if not entry.get('is_restday') and entry['card_in'] and entry['card_out']:
		entry['work'] = (entry.get('work_hours') * 60) * 60

		if entry["lv_status"] == 3:
			entry['work'] = entry['work'] / 2
		
		
		elif entry["lv_status"] == 2:
			entry['work'] = entry['work'] / 2

		elif entry["lv_status"] == 1:
			entry['work'] = 0

		else:
			if entry["is_halfday"] == 1:
				entry['work'] = entry['work'] / 2

	elif entry.get('ob_status') == 1:
		entry['work'] = (entry.get('work_hours') * 60) * 60
		if entry["is_halfday"] == 1:
			entry['work'] = entry['work'] / 2

	return entry

def get_overtime(entry):
	if frappe.db.get_single_value('Timekeeping Settings', 'strict_otcard'):
		if entry.get('linked_ot') and entry.get('card_out'):
			if entry.get('card_out') > entry.get('time_out'):
				if entry.get('ot_out') > entry.get('card_out'):
					entry['overtime'] = abs((entry.get('ot_in') - entry.get('card_out')).total_seconds())

	return entry

def get_ndiff(entry):	
	#late nightdiff
	if entry.get('card_in') and entry.get('card_out'):
		if entry.get('card_out') > entry.get('nd_start'):
			entry['nightdiff'] = abs((entry.get('card_out') - entry.get('nd_start')).total_seconds())
			if entry.get('card_out') > entry.get('nd_end'):
				entry['nightdiff'] = abs((entry.get('nd_start') - entry.get('nd_end')).total_seconds())

	#early nightdiff
		nd_early = get_datetime(str(entry.get('target_date')) +" "+ str("06:00:00") )
		if get_datetime(entry.get('card_in')) < nd_early :

	#OLD ND Code
	#if entry.get('time_out') > entry.get('nd_start'):
	#	entry['nightdiff'] += (entry.get('time_out') - entry.get('nd_start')).total_seconds()
	#	if entry.get('time_out') > entry.get('nd_end'):
	#		entry['nightdiff'] += (entry.get('nd_start') - entry.get('nd_end')).total_seconds()

	return entry

def get_late(entry):
	if not entry.get('ex_tardiness'):
		if entry.get('lv_status') == 2 and entry['card_in']: #get late if leave is 1sthalf halfday
			if entry.get('card_in') > entry.get('break_end'):
				entry['late'] += (entry.get('card_in') - entry.get('break_end')).total_seconds()

		elif entry.get('lv_status') == 3 and entry['card_in']: #get late if leave is 2ndhalf halfday
			if entry.get('card_in') > entry.get('time_in'):
				entry['late'] += (entry.get('card_in') - entry.get('time_in')).total_seconds()

		else: #get normal late if no leave
			if entry.get('card_in') and entry.get('lv_status') != 1:
				if entry.get('ob_status') == 1 and entry.get('ob_in') < entry.get('card_in'): #if has OB and is lesser than card in
					if entry.get('ob_in') > entry.get('break_end') + datetime.timedelta(minutes=entry.get('grace')) : #if OB is in second half
						entry['late'] += abs((entry.get('ob_in') - entry.get('break_end')).total_seconds())
					else: #if OB is in first half
						if entry.get('ob_in') > entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')) :
							entry['late'] += abs((entry.get('ob_in') - entry.get('time_in')).total_seconds())
				else: 
					if entry.get('card_in') > entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')):
						if frappe.db.get_single_value('Timekeeping Settings', 'graceperiod_late'):
							entry['late'] += ( entry.get('card_in') - entry.get('time_in') - datetime.timedelta(minutes=entry.get('grace')) ).total_seconds()
						else:
							entry['late'] += (entry.get('card_in') - entry.get('time_in')).total_seconds()
			
			else: #if no card in check for OB
				if entry.get('ob_status') == 1:
					if entry.get('ob_in') > entry.get('break_end'): #if OB is in second half
						entry['late'] += abs((entry.get('ob_in') - entry.get('break_end')).total_seconds())
					else:
						if entry.get('ob_in') > entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')) :
							entry['late'] += abs((entry.get('ob_in') - entry.get('time_in')).total_seconds())

		#break_out
		if not entry['is_leave'] and not entry['is_holiday'] and not entry['is_ob'] and entry['card_in']:
			if entry['break_out'] and entry['break_in']:
				entry['break'] = (entry.get('break_mins') * 60)
				if entry['break_out'] < entry['break_start']:
					b_diff = entry['break_start'] - entry['break_out']
					entry['undertime'] += b_diff.total_seconds()
					entry['work'] -= b_diff.total_seconds()
					entry['break'] -= b_diff.total_seconds()

				if entry['break_in'] > entry['break_end'] + datetime.timedelta(minutes=entry.get('b_grace')):
					b_diff = entry['break_in'] - entry['break_end']
					entry['late'] += b_diff.total_seconds()
					entry['work'] -= b_diff.total_seconds()
					entry['break'] -= b_diff.total_seconds()

	return entry

def get_undertime(entry):
	if not entry.get('ex_tardiness'):
		#if entry.get('is_flexible'):
		#	if entry.get('work') < (entry.get('worker_secs') + entry.get('late') ):
		#		entry['undertime'] += entry.get('work') - entry.get('worker_secs')

		if entry.get('lv_status') == 2 and entry['card_out']: #get undertime if leave is 1sthalf halfday
			if entry.get('ob_status') == 1:
				if entry.get('ob_out') < entry.get('time_out'):
					entry['undertime'] += abs((entry.get('ob_out') - entry.get('time_out')).total_seconds())
			else:
				if entry.get('card_out') < entry.get('time_out'):
					entry['undertime'] += abs((entry.get('card_out') - entry.get('time_out')).total_seconds())

		elif entry.get('lv_status') == 3 and entry['card_out']: #get undertime if leave is 2ndhalf halfday
			if entry.get('ob_status') == 1:
				if entry.get('ob_out') < entry.get('break_start'):
					entry['undertime'] += abs((entry.get('ob_out') - entry.get('break_start')).total_seconds())
			else:
				if entry.get('card_out') < entry.get('break_start'):
					entry['undertime'] += abs((entry.get('card_out') - entry.get('break_start')).total_seconds())
		else:	
			if entry.get('card_out') and entry.get('lv_status') != 1:
				if entry.get('ob_status') == 1:
					if entry.get('card_out') > entry.get('ob_out'):
						if entry.get('card_out') < entry.get('time_out'):
							entry['undertime'] += abs((entry.get('card_out') - entry.get('time_out')).total_seconds())
					else:
						if entry.get('ob_out') < entry.get('time_out'):
							entry['undertime'] += abs((entry.get('ob_out') - entry.get('time_out')).total_seconds())
				else:
					if entry.get('card_out') < entry.get('time_out'):
						entry['undertime'] += abs((entry.get('card_out') - entry.get('time_out')).total_seconds())
			else: #if no card in check for OB
				if entry.get('ob_status') == 1:
					if entry.get('ob_out') < entry.get('break_end'): #if OB is in second half
						entry['undertime'] += abs((entry.get('ob_out') - entry.get('break_end')).total_seconds())
					else:
						if entry.get('ob_out') < entry.get('time_out'):
							entry['undertime'] += abs((entry.get('ob_out') - entry.get('time_out')).total_seconds())

	return entry

def get_absent(entry):
	if not entry.get('is_restday') and not entry['is_holiday'] and not entry.get('ob_status'):
		if not entry.get('card_in') and not entry.get('card_out'):
			if entry.get('lv_status') == 2:
				if entry['is_lwop'] == 1:
					entry['is_absent'] = 1
					entry["work"] = 0
					
			elif entry.get('lv_status') == 3:
				if entry['is_lwop'] == 1:
					entry['is_absent'] = 1
					entry["work"] = 0

			elif entry.get('lv_status') == 1:
				if entry['is_lwop'] == 1:
					entry["work"] = 0
			else:
				if entry.get('lv_status') != 1:
					entry['is_absent'] = 1
					entry["work"] = 0
					entry["late"] = 0
					entry["undertime"] = 0

		elif not entry.get('card_in'):
			if entry.get('lv_status') == 2:
				entry['is_absent'] = 1
				entry['is_halfday'] = 1
				if entry['is_lwop'] == 1:
					entry['is_absent'] = 1
					entry['is_halfday'] = 1
					entry["work"] = 0
					
			elif entry.get('lv_status') == 3:
				entry['is_absent'] = 1
				entry['is_halfday'] = 1
				if entry['is_lwop'] == 1:
					entry['is_absent'] = 1
					entry['is_halfday'] = 1
					entry["work"] = 0

			elif entry.get('lv_status') == 1:
				if entry['is_lwop'] == 1:
					entry["work"] = 0
			else:
				if entry.get('lv_status') != 1:
					entry['is_absent'] = 1
					entry["work"] = 0
					entry["late"] = 0
					entry["undertime"] = 0

	if entry.get('is_restday') and not entry.get('lv_status') and not entry.get('ob_status'):
		entry["work"] = 0
		entry["late"] = 0
		entry["undertime"] = 0
		entry["is_absent"] = 0

	if entry.get('lv_status') > 1 and not entry.get('card_out'):
		entry["work"] = 0
		entry["is_absent"] = 1
		entry["is_halfday"] = 1

	if not entry.get('card_out') and not entry.get('is_restday') and not entry.get('is_holiday') and not entry.get('lv_status') and not entry.get('ob_status'):
		entry["work"] = 0
		entry["late"] = 0
		entry["undertime"] = 0
		entry["is_absent"] = 1

	if entry.get('lv_status') == 1:
		entry["work"] = 0
		entry["late"] = 0
		entry["undertime"] = 0
		entry["is_absent"] = 0

	if entry.get('is_restday'):
		entry["late"] = 0
		entry["undertime"] = 0
		entry["is_absent"] = 0
		
	return entry

def get_final_processing(entry):
	entry['work'] -= entry['late']
	entry['work'] -= entry['undertime']

	if not entry.get('is_attendance_base'):
		entry["work"] = 0 if entry.get('is_restday') else (entry.get('work_hours') * 60) * 60
		entry["is_absent"] = 0
		entry["break"] = 0
		entry["late"] = 0
		entry["nightdiff"] = 0
		entry["overtime"] = 0
		entry["undertime"] = 0

	ch_tr=0
	ch = flt(frappe.db.get_single_value('Timekeeping Settings', 'consider_halfday'), 8)		
	if flt(entry["late"], 8) >= ch and ch > 0 and entry.get('lv_status') != 2 and entry.get('lv_status') != 1:		
		entry["late"] = 0
		entry["absent"] = 1
		entry["is_halfday"] = 1
		entry['work'] = (entry.get('work_hours') * 60 * 60) / 2
		ch_tr=1

	chu_tr=0
	chu = flt(frappe.db.get_single_value('Timekeeping Settings', 'ut_consider_halfday'), 8)		
	if flt(entry["undertime"], 8) >= chu and chu > 0 and entry.get('lv_status') != 3 and entry.get('lv_status') != 1:		
		entry["undertime"] = 0		
		entry["absent"] = 1		
		entry["is_halfday"] = 1		
		entry['work'] = (entry.get('work_hours') * 60 * 60) / 2
		chu_tr=1

	if chu_tr == 1 and ch_tr == 1:
		entry["late"] = 0		
		entry["undertime"] = 0
		entry["is_halfday"] = 0
		entry['work'] = 0
		entry["is_absent"] = 1

	strict_card = flt(frappe.db.get_single_value('Timekeeping Settings', 'strict_nocard'), 8)	
	if entry.get('lv_status') != 1 and not entry.get('card_out') and strict_card:
		entry['is_absent'] = 1
		entry["is_halfday"] = 0
		entry["work"] = 0
		entry["late"] = 0
		entry["undertime"] = 0

	strict_card = flt(frappe.db.get_single_value('Timekeeping Settings', 'strict_nocard'), 8)	
	if entry.get('lv_status') != 1 and not entry.get('card_in') and strict_card:
		entry['is_absent'] = 1
		entry["is_halfday"] = 0
		entry["work"] = 0
		entry["late"] = 0
		entry["undertime"] = 0

	return entry

def get_tags(entry):
	#leave tags
	if entry['lv_status'] == 1:
		entry["tags"] += "<span class='label label-success'>"+cstr(entry['leave_name'])+"</span>"
	elif entry['lv_status'] == 2:
		entry["tags"] += "<span class='label label-success'>"+cstr(entry['leave_name'])+" 1sthalf </span>"
	elif entry['lv_status'] == 3:
		entry["tags"] += "<span class='label label-success'>"+cstr(entry['leave_name'])+" 2ndhalf </span>"
	entry["tags"] += "<span class='label label-danger'> LWOP </span> " if entry['is_lwop'] > 0 else ""		
	entry["tags"] += "<span class='label label-danger'> Halfday </span> " if entry['is_halfday'] > 0 else ""
	entry["tags"] += "<span class='label label-success'> Double Holiday </span> " if entry['is_db_holiday'] > 0 else ""
	#ot tags
	ot_map = get_overtime_map()
	if entry.get('linked_ot') and entry.get('overtime'):
		is_saturday = 1 if getdate(entry.get('target_date')).weekday() == 5 else 0
		is_sunday = 1 if getdate(entry.get('target_date')).weekday() == 6 else 0
		is_excess = 1 if entry.get('overtime') > 28800 else 0
		is_ndiff = 1 if entry.get('nightdiff') > 28800 else 0
		is_db_holiday = entry.get('is_db_holiday')
		#[RD][HO][SHO][DHO][SUN][SAT][EX][ND]
		overtime_type = [entry.get('is_restday'), entry.get('is_holiday'), entry.get('is_sp_holiday'), is_db_holiday, is_sunday, is_saturday, is_excess, is_ndiff]
		overtime_type = ''.join(str(x) for x in overtime_type)
		if overtime_type in ot_map:
			entry["tags"] += " <span class='label label-success'>"+ot_map[overtime_type]['name']+"</span> " if entry['overtime'] > 0 else ""
		else:
			entry["tags"] += " <span class='label label-success'>OT-"+overtime_type+"</span> " if entry['overtime'] > 0 else ""
			
	#ut tags
	if entry.get('linked_ut'):
		entry["tags"] += " <span class='label label-danger'> Approved Undertime </span> "
	elif entry.get('undertime') > 0:
		entry["tags"] += " <span class='label label-danger'> Undertime </span> "

	entry["tags"] += " <span class='label label-success'> Excused Tardiness </span> " if entry.get('ex_tardiness') else ""
	entry["tags"] += " <span class='label label-danger'> Absent </span> " if entry['is_absent'] == 1 else ""
	entry["tags"] += " <span class='label label-danger'> Late </span> " if entry['late'] > 0 else ""
	entry["tags"] += " <span class='label label-info'>"+ entry['holiday_name'] +"</span>" if entry['is_holiday'] == 1 else ""
	entry["tags"] += " <span class='label label-info'> Special Non-Working </span>" if entry['is_sp_holiday'] == 1 else ""
	entry["tags"] += " <span class='label label-success'> Official Business </span> " if entry['is_ob'] else ""
	entry["tags"] += "<span class='label label-success'>"+cstr(entry['leave_name'])+"</span>" if entry['is_leave'] > 0 else ""
	
	if entry['is_restday']:
		entry["tags"] += "<span class='label label-info'> Rest Day </span> "
	else:
		if not entry['card_in'] and entry['is_attendance_base']:
			entry["tags"] += " <span class='label label-warning'> No Card IN </span> "

		if not entry['card_out'] and entry['is_attendance_base']:
			entry["tags"] += " <span class='label label-warning'> No Card OUT </span> "

	return entry

def get_schedule(employee, pay_from, pay_to):
	schedule = frappe.db.sql("""SELECT employee, company, work_shift, work_hours, break_mins, target_date, shift_type, 
		datetime_in, datetime_out, pre_shift, post_shift, break_start, break_end, nd_start, nd_end
		FROM `tabWork Schedule` 
		WHERE employee = %(employee)s AND target_date >= %(from_date)s AND target_date <= %(to_date)s
		ORDER BY target_date ASC""",{
			"employee": employee,
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)

	return schedule

def get_shift_map():
	shift_map = {}
	shifts = frappe.db.sql("""SELECT `name`, work_hours, override_hrs, grace_period, b_grace_period, is_restday,
			is_flexible, setup_preshift, setup_postshift, ignore_late
		FROM `tabWork Shift` """, as_dict=True)
	
	for d in shifts:
		if flt(d.override_hrs) > 0:		
			work_hours = d.override_hrs		
		else:		
			work_hours = d.work_hours

		shift_map[d.name] = {
			"work_hours": work_hours,
			"grace_period": d.grace_period,
			"b_grace_period": d.b_grace_period,
			"is_restday": d.is_restday,
			"is_flexible": d.is_flexible,
			"ignore_late": d.ignore_late,
			"setup_preshift": d.setup_preshift,
			"setup_postshift": d.setup_postshift,
		}

	return shift_map

def get_holiday_list(company, location, from_date, to_date):
	holidays = frappe.db.sql("""SELECT holiday_name, holiday_date, is_special FROM `tabHoliday` 
		WHERE company = %s AND location = %s AND holiday_date >= %s AND holiday_date <= %s
		ORDER BY holiday_date ASC""",(company, location, from_date, to_date), as_dict=True)

	return holidays

def get_leave_list(employee, from_date, to_date):
	leave_list = frappe.db.sql("""SELECT L.`name`, L.employee, L.leave_type, LA.leave_date, LA.is_half_day, LA.is_second_half, LA.is_holiday, LA.is_excluded, L.is_lwop
		FROM `tabLeave Application Table` LA
		INNER JOIN `tabLeave Application` L ON L.`name` = LA.parent
		WHERE L.employee = %s AND LA.leave_date >= %s AND LA.leave_date <= %s AND L.docstatus = '1'
		ORDER BY LA.leave_date ASC""",(employee, from_date, to_date), as_dict=True)

	return leave_list

def get_ob_list(employee, from_date, to_date):
	ob_apps = frappe.db.sql("""SELECT OBA.`name`, OBAT.target_date, OBAT.from_time, OBAT.to_time, OBAT.hrs, OBAT.is_holiday, OBAT.is_excluded 
		FROM `tabOfficial Business Application Table` OBAT
		INNER JOIN `tabOfficial Business Application` OBA  ON OBAT.parent = OBA.`name`
		WHERE OBA.employee = %s AND OBA.workflow_state = 'Approved' AND OBAT.target_date >= %s 
		AND OBAT.target_date <= %s AND OBAT.is_excluded = 0 """,(employee, from_date, to_date), as_dict=1)

	return ob_apps

def get_ot_list(employee, from_date, to_date):
	ot_apps = frappe.db.sql("""SELECT `name`, total_hrs, target_date, from_date, to_date, from_time, to_time FROM `tabOvertime Application` 
		WHERE workflow_state = 'Approved' AND employee = %s AND target_date >= %s AND target_date <= %s """, (employee, from_date, to_date), as_dict=1)
	return ot_apps

def get_ut_list(employee, from_date, to_date):
	ut_apps = frappe.db.sql("""SELECT `name`, from_time, to_time, from_date FROM `tabUndertime Application` 
		WHERE workflow_state = 'Approved' AND employee = %s AND from_date >= %s AND from_date <= %s """, (employee, from_date, to_date), as_dict=1)
	return ut_apps

def get_ext_list(employee, from_date, to_date):
	ext_apps = frappe.db.sql("""SELECT `name`, from_time, to_time, `date`, `type` FROM `tabExcuse Tardiness Application` 
		WHERE workflow_state = 'Approved' AND employee = %s AND `date` >= %s AND `date` <= %s """, (employee, from_date, to_date), as_dict=1)
	return ext_apps

def get_card_within(pre_shift, post_shift, timecard_list):
	cards = []
	for tc in timecard_list:
		if pre_shift <= tc.card_datetime <= post_shift:
			cards.append({
				"card_name":tc.name,
				"card_time":tc.time,
				"card_datetime": tc.card_datetime,
				"card_type": tc.card_type
			})
	return cards

def get_timecard_list(bio, pay_from, pay_to):
	timecard_list = frappe.db.sql("""SELECT TIMESTAMP(date, time) as card_datetime, card_type,name,`time` FROM `tabTime Card` 
		WHERE biometrics_id = %(bio)s AND date >= %(from_date)s AND date <= %(to_date)s
		ORDER BY date, time """,{
			"bio": bio,
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)
	return timecard_list

def get_overtime_map():
	ot_map = {}
	ot = frappe.db.sql(""" SELECT ot_name, ot_code, ot_rate FROM `tabOvertime Rates` """, as_dict=1)
	for t in ot:
		ot_map[t.ot_code] = {
			"name": t.ot_name,
			"rate": t.ot_rate,
		}
	return ot_map

def get_defaults(emp, sched, shift_map):
	entry = {
		#employe settings
		"employee": emp.name,
		"worker_hrs": emp.no_hours,
		"worker_secs": (emp.no_hours * 60) * 60,
		"is_attendance_base": emp.is_attendance_base,
		#schedule settings
		"target_date": getdate(sched.datetime_in),
		"work_shift": sched.work_shift,
		"pre_shift": add_to_date(sched.datetime_in, hours= (0 - shift_map[sched.work_shift]['setup_preshift']) ),
		"post_shift": add_to_date(sched.datetime_out, hours=shift_map[sched.work_shift]['setup_postshift']),
		"time_in": sched.datetime_in,
		"time_out": sched.datetime_out,
		"break_start": sched.break_start,
		"break_end": sched.break_end,
		"nd_start": sched.nd_start,
		"nd_end": sched.nd_end,
		#shift policy
		"work_hours": shift_map[sched.work_shift]['work_hours'],
		"break_mins": sched.break_mins,
		"grace": shift_map[sched.work_shift]['grace_period'],
		"b_grace": shift_map[sched.work_shift]['b_grace_period'],
		"is_flexible": shift_map[sched.work_shift]['is_flexible'],		
		"is_restday": shift_map[sched.work_shift]['is_restday'],
		"ignore_late": shift_map[sched.work_shift]['ignore_late'],
		#general policy
		"is_processed": 0,
		#timecard data
		"card_in": "",
		"card_out": "",			
		"break_out": "",
		"break_in": "",
		#basic attendance
		"work": 0.0,
		"late": 0.0,
		"break": 0.0,
		"undertime": 0.0,
		"nightdiff": 0.0,
		"is_absent": 0,
		"is_halfday": 0,
		#Applications
		#OT
		"linked_ot": "",
		"overtime": 0.0,
		"ot_in": "",
		"ot_out": "",
		#LEAVE
		"linked_leave": "",
		"leave_name": "",
		"lv_status": 0,
		"is_leave": 0,
		"is_lwop": 0,
		#OB
		"linked_ob": "",
		"is_ob": 0,
		"ob_in": "",
		"ob_out": "",
		"ob": 0.0,
		#UT
		"linked_ut": "",
		"ut_from": "",
		"ut_to": "",
		#HOLIDAY
		"is_holiday": 0,
		"is_sp_holiday": 0,
		"is_db_holiday": 0,
		"holiday_name": "",
		"linked_holiday": "",
		"ex_tardiness": 0,
		"tags": "",		
	}
	return entry
