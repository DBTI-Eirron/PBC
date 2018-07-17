from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, get_datetime
from frappe import _

def get_attendance(entry, leaves, holidays):
	#official business
	ob_apps = frappe.db.sql("""SELECT OBA.`name` FROM `tabOfficial Business Application Table` OBAT
		INNER JOIN `tabOfficial Business Application` OBA  ON OBAT.parent = OBA.`name`
		WHERE OBA.workflow_state = 'Approved' AND %s BETWEEN OBA.from_date AND OBA.to_date 
		AND OBA.employee = %s LIMIT 1""",( entry.get('target_date'), entry.get('employee') ), as_dict=1)

	for ob in ob_apps:
		entry['is_ob'] = 1
		entry['linked_ob'] = ob.name
		entry["is_absent"] = 0
		entry['is_lwop'] = 0

	if holidays:
		for h in holidays:
			if datetime.datetime.strftime(h['holiday_date'], '%Y-%m-%d') == entry['target_date']:
				entry["is_absent"] = 0
				entry['is_lwop'] = 0
				entry["undertime"] = 0
				entry["late"] = 0
				entry['holiday_name'] = h['holiday_name']
				entry['is_holiday'] = 1
				if h['is_special'] == 1:
					entry['is_sp_holiday'] = 1

				if not entry['card_in'] or not entry['card_out']:
					entry['work'] = (entry.get('work_hours') * 60) * 60

	#leaves	
	for l in leaves:
		if  datetime.datetime.strftime(l['leave_date'], '%Y-%m-%d') == entry['target_date']:
			if l['is_excluded'] != 1:
				entry['leave_name'] = l['leave_type']
				entry["is_absent"] = 0
				entry["undertime"] = 0
				entry["late"] = 0
				entry['is_leave'] = 1
				if not entry['card_in'] or not entry['card_out']:
					entry['work'] = (entry.get('work_hours') * 60) * 60

				if l['is_lwop'] == 1:
					entry['is_lwop'] = 1
					entry['is_leave'] = 0
					entry['work'] = 0
				
				if l['is_half_day'] == 1:
					entry["is_halfday"] = 1

	if not entry.get('is_restday') and entry['card_in'] and entry['card_out']:
		entry['work'] = (entry.get('work_hours') * 60) * 60
		if entry["is_halfday"] == 1:
			entry['work'] = entry['work'] / 2

		#late
		if not entry['is_leave'] and not entry['is_holiday'] and not entry['is_ob'] and not entry['is_lwop']:
			if entry.get('card_in') > entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')):
				if frappe.db.get_single_value('Timekeeping Settings', 'graceperiod_late'):
					entry['late'] += ( entry.get('card_in') - (entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')))  ).total_seconds()
				else:
					entry['late'] += (entry.get('card_in') - entry.get('time_in')).total_seconds()

				entry['work'] -= entry['late']
				if entry.get("is_processed") and entry.get("ignore_late"):
					entry['late'] = 0

		#break
		if not entry['is_leave'] and not entry['is_holiday'] and not entry['is_ob'] :
			if entry['break_out'] and entry['break_in']:
				entry['break'] = (d.get('break_mins') * 60)
				if entry['break_out'] < entry['break_start']:
					b_diff = d['break_start'] - d['break_out']
					entry['undertime'] += b_diff.total_seconds()
					entry['work'] -= b_diff.total_seconds()
					entry['break'] -= b_diff.total_seconds()


				if entry['break_in'] > entry['break_end'] + datetime.timedelta(minutes=d['b_grace']):
					b_diff = d['break_in'] - d['break_end']
					entry['late'] += b_diff.total_seconds()
					entry['work'] -= b_diff.total_seconds()
					entry['break'] -= b_diff.total_seconds()

		#undertime
		if not entry['is_leave'] and not entry['is_holiday'] and not entry['is_ob'] and not entry['is_lwop']:
			#if entry.get('is_flexible'):
				#if entry.get('work') < (entry.get('worker_secs') + entry.get('late') ):
				#	entry['undertime'] += entry.get('work') - entry.get('worker_secs')
				#	entry['work'] -= entry['undertime']
		
			if entry['card_out'] < entry['time_out']:
				entry['undertime'] += abs((entry.get('card_out') - entry.get('time_out')).total_seconds())
				entry['work'] -= entry['undertime']

		#overtime
		if not entry.get('approved_ot_only'):
			if entry.get('card_in') and entry.get('card_out'):
				if entry.get('card_out') > entry.get('time_out'):
					entry['overtime'] = (entry.get('card_out') - entry.get('time_out')).total_seconds()
		else:
			ot_apps = frappe.db.sql("""SELECT `name`, total_hrs FROM `tabOvertime Application` 
				WHERE workflow_state = 'Approved' AND target_date = %s 
				AND employee = %s """, ( entry.get('target_date'), entry.get('employee') ), as_dict=1)

			for ot in ot_apps:
				entry['overtime'] += (ot.total_hrs * 60) * 60
				entry['linked_ot'] = ot.name
	elif entry.get('is_restday'):
		#overtime
		ot_apps = frappe.db.sql("""SELECT `name`, total_hrs FROM `tabOvertime Application` 
			WHERE workflow_state = 'Approved' AND target_date = %s 
			AND employee = %s """, ( entry.get('target_date'), entry.get('employee') ), as_dict=1)

		for ot in ot_apps:
			entry['overtime'] += (ot.total_hrs * 60) * 60
			entry['linked_ot'] = ot.name	
	else:
		if not entry['is_leave'] and not entry['is_holiday'] and not entry['is_ob'] and not entry['is_lwop']:
			entry["is_absent"] = 1

	#if flexible
	if entry.get('is_flexible'):
		if entry.get('work') < (entry.get('worker_secs')):
			entry['undertime'] += abs(entry.get('work') - entry.get('worker_secs'))
			entry['work'] += entry['late']
			entry['late'] = 0
			entry['work'] -= entry['undertime']

	#nightdiff
	#if get_datetime(entry.get('card_out')) > get_datetime(entry.get('nd_start')):
	#	frappe.throw("nightdiff")


	if entry["late"] > frappe.db.get_single_value('Timekeeping Settings', 'consider_halfday') and frappe.db.get_single_value('Timekeeping Settings', 'consider_halfday') > 0:
		entry["is_halfday"] = 1
	#is_attendance_base
	if not entry.get('is_attendance_base'):
		entry["work"] = 0 if entry.get('is_restday') else (entry.get('work_hours') * 60) * 60
		entry["is_absent"] = 0
		entry["break"] = 0
		entry["late"] = 0
		entry["nightdiff"] = 0
		entry["overtime"] = 0
		entry["undertime"] = 0

def get_holidays(d, holidays):
	if holidays:
		is_holiday = 0
		is_special = 0
		for h in holidays:
			if datetime.datetime.strftime(h['holiday_date'], '%Y-%m-%d') == d['target_date']:
				is_holiday = 1
				if h['is_special'] == 1:
					is_special = 1
			d['holiday_name'] = h['holiday_name']
		d['is_holiday'] = is_holiday
		d['is_sp_holiday'] = is_special

	return d

def get_leaves(d, leave_list):
	for l in leave_list:
		if  datetime.datetime.strftime(l['leave_date'], '%Y-%m-%d') == d['target_date']:
			if l['is_excluded'] != 1:
				d['is_leave'] = 1
				if l['is_half_day'] == 1:
					d["is_halfday"] = 1

	return d

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
	shifts = frappe.db.sql("""SELECT `name`, grace_period, b_grace_period, is_restday,
			is_flexible, setup_preshift, setup_postshift, ignore_late
		FROM `tabWork Shift` """, as_dict=True)

	for d in shifts:
		shift_map[d.name] = {
			"grace_period": d.grace_period,
			"b_grace_period": d.b_grace_period,
			"is_restday": d.is_restday,
			"is_flexible": d.is_flexible,
			"ignore_late": d.ignore_late,
			"setup_preshift": d.setup_preshift,
			"setup_postshift": d.setup_postshift,
		}

	return shift_map

def get_holiday_list(company, from_date, to_date):
	holidays = frappe.db.sql("""SELECT holiday_name, holiday_date, is_special FROM `tabHoliday` 
		WHERE company = %s AND holiday_date >= %s AND holiday_date <= %s
		ORDER BY holiday_date ASC""",(company, from_date, to_date), as_dict=True)

	return holidays

def get_leave_list(employee, from_date, to_date):
	leave_list = frappe.db.sql("""SELECT L.`name`, L.employee, L.leave_type, LA.leave_date, LA.is_half_day, LA.is_holiday, LA.is_excluded, L.is_lwop
		FROM `tabLeave Application Table` LA
		INNER JOIN `tabLeave Application` L ON L.`name` = LA.parent
		WHERE L.employee = %s AND LA.leave_date >= %s AND LA.leave_date <= %s AND L.docstatus = '1'
		ORDER BY LA.leave_date ASC""",(employee, from_date, to_date), as_dict=True)

	return leave_list

def get_card_within(pre_shift, post_shift, timecard_list):
	cards = []
	for tc in timecard_list:
		if pre_shift <= tc.card_datetime <= post_shift:
			cards.append({
				'card_datetime': tc.card_datetime,
				'card_type': tc.card_type
			})
	return cards

def get_timecard_list(bio, pay_from, pay_to):
	timecard_list = frappe.db.sql("""SELECT TIMESTAMP(date, time) as card_datetime, card_type FROM `tabTime Card` 
		WHERE biometrics_id = %(bio)s AND date >= %(from_date)s AND date <= %(to_date)s
		ORDER BY date, time """,{
			"bio": bio,
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)
	return timecard_list