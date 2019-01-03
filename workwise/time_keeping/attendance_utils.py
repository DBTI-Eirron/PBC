from __future__ import unicode_literals
import frappe, datetime, math
from frappe.utils import cint, cstr, flt, nowdate, add_days, getdate, fmt_money, get_datetime, add_to_date
from frappe import _

def get_attendance(entry, leaves, holidays, obs, ots, uts, ext):
	if entry.get("override_in"):
		entry['card_in'] = entry.get("override_in")

	if entry.get("override_out"):
		entry['card_out'] = entry.get("override_out")

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
	get_overtime(entry, ots)
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

def get_overtime(entry, ot_apps):
	ot_map = get_overtime_map()
 	strict_otcard = frappe.db.get_single_value('Timekeeping Settings', 'strict_otcard')
	ot_list = []
	total_ot = 0.0

	#Get Nigthdiff Setup
	if entry.get('nd_start') and entry.get('nd_end'):
		nd_start = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_start')) )
		nd_end = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_end')) )
		if entry.get('nd_start') > entry.get('nd_end'):
			nd_end = get_datetime( str( add_days(entry.get('target_date'), 1) ) +" "+ str(entry.get('nd_end')) )

		nd_early_start = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_end')) )

	if ot_apps:
		for d in ot_apps:
			ot_hrs, ot_nd, ot_normal = 0, 0, 0
			if getdate(d.get('target_date')) == entry.get('target_date'):
				linked_ot = d.name
				ot_in = get_datetime( str(d.from_date) +" "+ str(d.from_time) )
				ot_out = get_datetime( str(d.to_date) +" "+ str(d.to_time) )
				is_saturday = 1 if getdate(entry.get('target_date')).weekday() == 5 else 0
				is_sunday = 1 if getdate(entry.get('target_date')).weekday() == 6 else 0
				is_db_holiday = entry.get('is_db_holiday')
				
				#get Card Out if Straight OT
				if ot_out and entry.get('straight_ot'):
					entry['card_out'] = ot_out

				#get OT Start based from interval
				if entry.get('ot_start_delay'):
					ot_int_start = add_to_date(entry.get('time_out'), hours=(entry.get('ot_start_delay') / 60) )
					if ot_int_start > ot_in:
						ot_in = ot_int_start

				#Always follow whichever is lower between card_out and ot_out
				if entry.get('card_out') and strict_otcard:
					if entry.get('card_out') < ot_out:
						ot_out = entry.get('card_out')
				
				#Get Normal OT before ND and Should also consider early ND OT
				if ot_in < nd_start:
					if ot_out >= nd_start:
						if ot_in < nd_early_start:
							ot_normal += abs((nd_early_start - ot_out).total_seconds())
						else:
							ot_normal += abs((ot_in - nd_start).total_seconds())
					else:
						if ot_in < nd_early_start:
							ot_normal += abs((nd_early_start - ot_out).total_seconds())
						else:
							ot_normal += abs((ot_in - ot_out).total_seconds())

				#Get Additional Normal OT After ND
				if ot_out >= nd_end:
					ot_normal += abs((nd_end - ot_out).total_seconds())

				#Get ND OT
				if ot_out > nd_start:
					if ot_out > nd_end:
						ot_nd = abs((nd_start - nd_end).total_seconds())
					else:
						ot_nd = abs((nd_start - ot_out).total_seconds())

				#Get early ND OT
				if ot_in < nd_early_start:
					if ot_out > nd_early_start:
						ot_nd = abs((ot_in - nd_early_start).total_seconds())
					else:
						ot_nd = abs((ot_in - ot_out).total_seconds())

				#[RD][HO][SHO][DHO][SUN][SAT][EX][ND]
				if ot_normal > 0:					
					if ot_normal > 28800:
						ot_normal = 28800

					if d.break_hrs:
						ot_normal -= flt(d.break_hrs, 8) * 60 * 60

					if entry.get('ot_interval'):
						ot_normal = (entry.get('ot_interval') * 60) * int(ot_normal / (entry.get('ot_interval') * 60))

					ot_normal_code = [entry.get('is_restday'), entry.get('is_holiday'), entry.get('is_sp_holiday'), is_db_holiday, is_sunday, is_saturday, 0, 0]
					ot_normal_code = ''.join(str(x) for x in ot_normal_code)
					ot_list.append({
						"employee": entry.get('employee'),
						"target_date": entry.get('target_date'),
						"ot_type": "OT_NORMAL",
						"ot_code": ot_normal_code,
						"ot_hrs": ot_normal / 60 / 60,
						"linked_ot": d.name,
						"ot_tag": "",
					})
					ot_hrs += ot_normal

				if ot_nd > 0: 
					if entry.get('ot_interval'):
						ot_nd = (entry.get('ot_interval') * 60) * int(ot_nd / (entry.get('ot_interval') * 60))

					ot_nd_code = [entry.get('is_restday'), entry.get('is_holiday'), entry.get('is_sp_holiday'), is_db_holiday, is_sunday, is_saturday, 0, 1]
					ot_nd_code = ''.join(str(x) for x in ot_nd_code)
					ot_list.append({
						"employee": entry.get('employee'),
						"target_date": entry.get('target_date'),
						"ot_type": "OT_ND",
						"ot_code": ot_nd_code,
						"ot_hrs": ot_nd  / 60 / 60,
						"linked_ot": d.name,
						"ot_tag": "",
					})
					ot_hrs += ot_nd

				if ot_hrs > 28800:
					ot_ex = (ot_hrs - 28800)
					if entry.get('ot_interval'):
						ot_ex = (entry.get('ot_interval') * 60) * int(ot_ex / (entry.get('ot_interval') * 60))

					ot_ex_code = [entry.get('is_restday'), entry.get('is_holiday'), entry.get('is_sp_holiday'), is_db_holiday, is_sunday, is_saturday, 1, 0]
					ot_ex_code = ''.join(str(x) for x in ot_ex_code)
					ot_list.append({
						"employee": entry.get('employee'),
						"target_date": entry.get('target_date'),
						"ot_type": "OT_EX",
						"ot_code": ot_ex_code,
						"ot_hrs": ot_ex / 60 / 60,
						"linked_ot": d.name,
						"ot_tag": "",
					})
					ot_hrs += ot_ex
				total_ot += ot_hrs

	for l in ot_list:
		overtime_type = l.get('ot_code')
		if overtime_type in ot_map:
			l["ot_tag"] += " <span class='label label-success'>"+ot_map[overtime_type]['name']+" "+cstr(l.get('ot_hrs')) +" Hrs </span> "
		else:
			l["ot_tag"] += " <span class='label label-success'>OT-"+overtime_type+"</span> "	

	entry['ot_list'] = ot_list
	entry['overtime'] = total_ot
	return entry

def get_ndiff(entry):
	if entry.get('nd_start') and entry.get('nd_end') and not frappe.db.get_single_value('Timekeeping Settings', 'ignore_nd'):
		#get nightdiff start and end
		nd_start = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_start')) )
		nd_end = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_end')) )
		if entry.get('nd_start') > entry.get('nd_end'):
			nd_end = get_datetime( str( add_days(entry.get('target_date'), 1) ) +" "+ str(entry.get('nd_end')) )		

		#normal nightdiff
		if entry.get('time_out') >= nd_start:
			if entry.get('card_in') and entry.get('card_out'):
				if entry.get('card_out') > nd_start:
					entry['nightdiff'] = abs((entry.get('card_out') - nd_start).total_seconds())
					if entry.get('card_out') > nd_end:
						entry['nightdiff'] = abs( (nd_start - nd_end).total_seconds())

		#early nightdiff
		nd_early_start = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_end')) )
		if entry.get('time_in') <= nd_early_start:
			if get_datetime(entry.get('card_in')) < nd_early_start:
				if get_datetime(entry.get('card_in')) < get_datetime(entry.get('time_in')):
					entry['nightdiff'] = abs(( get_datetime(entry.get('time_in')) - nd_early_start ).total_seconds())
				else:
					entry['nightdiff'] = abs(( get_datetime(entry.get('card_in')) - nd_early_start ).total_seconds())	

		

		#else:
		#	#get normal ot if approved nightdiff OT
		#	for d in entry.get('ot_list'):
		#		if d.get('ot_type') == "OT_ND":
		#			entry['nightdiff'] += d.get('ot_hrs')

		#OLD ND Code
		#if entry.get('time_out') > entry.get('nd_start'):
		#	entry['nightdiff'] += (entry.get('time_out') - entry.get('nd_start')).total_seconds()
		#	if entry.get('time_out') > entry.get('nd_end'):
		#		entry['nightdiff'] += (entry.get('nd_start') - entry.get('nd_end')).total_seconds()

	return entry

def get_late(entry):
	if not entry.get('ex_tardiness'):
		if entry.get('lv_status') == 2 and entry['card_in']: #get late if leave is 1sthalf halfday
			if entry.get('card_in') > entry.get('break_end') + datetime.timedelta(minutes=entry.get('b_grace')):
				entry['late'] += (entry.get('card_in') - entry.get('break_end')).total_seconds()

		elif entry.get('lv_status') == 3 and entry['card_in']: #get late if leave is 2ndhalf halfday
			if entry.get('card_in') > entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')):
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
						if entry['graceperiod_late']:
							entry['late'] += ( entry.get('card_in') - ( entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace'))) ).total_seconds()
							if entry.get('card_in') > entry.get('break_start'): #Reduce late based from Break Time
								if entry.get('card_in') > entry.get('break_end'): #Reduce late Beyond Break Time
									entry['late'] -= abs((entry.get('break_start') - entry.get('break_end')).total_seconds())
								else:
									entry['late'] -= abs((entry.get('card_in') - entry.get('break_start')).total_seconds())
						else:
							entry['late'] += (entry.get('card_in') - entry.get('time_in')).total_seconds()
							if entry.get('card_in') > entry.get('break_start'): #Reduce late based from Break Time
								if entry.get('card_in') > entry.get('break_end'): #Reduce late Beyond Break Time
									entry['late'] -= abs((entry.get('break_start') - entry.get('break_end')).total_seconds())
								else:
									entry['late'] -= abs((entry.get('card_in') - entry.get('break_start')).total_seconds())
			
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
		
		if entry.get('late_interval'):
			entry['late'] = (entry.get('late_interval') * 60) * int( entry.get('late') / (entry.get('late_interval') * 60))

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
					if entry.get('ob_out') < entry.get('break_end'): #if OB is in first half
						entry['undertime'] += abs((entry.get('break_end') - entry.get('time_out')).total_seconds())
						if entry.get('ob_out') < entry.get('break_start'): #Add undertime Beyond Break Time
							entry['undertime'] += abs((entry.get('ob_out') - entry.get('break_start')).total_seconds())
					else:
						if entry.get('ob_out') < entry.get('time_out'): #if OB is wholeday
							entry['undertime'] += abs((entry.get('ob_out') - entry.get('time_out')).total_seconds())
		
		if entry.get('ut_interval'):
			entry['undertime'] = (entry.get('ut_interval') * 60) * int( entry.get('undertime') / (entry.get('ut_interval') * 60))

	return entry

def get_absent(entry):
	if not entry.get('is_restday') and not entry['is_holiday'] and not entry.get('ob_status'):
		if not entry.get('card_in') and not entry.get('card_out'):
			if entry.get('lv_status') == 1 or entry.get('suspension') == 2:
				if entry['is_lwop'] == 1:
					entry['is_absent'] = 1
					entry["work"] = 0
					
			elif entry.get('lv_status') == 3 or entry.get('suspension') == 3:
				if entry['is_lwop'] == 1:
					entry['is_absent'] = 1
					entry["work"] = 0

			elif entry.get('lv_status') == 1 or entry.get('suspension') == 1:
				entry['is_absent'] = 0	
				if entry['is_lwop'] == 1:
					entry["work"] = 0
			else:
				if entry.get('lv_status') != 1 or entry.get('suspension') != 1:
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

	if (entry.get('lv_status') > 1 or entry.get('suspension') > 1) and not entry.get('card_out'):
		entry["work"] = 0
		entry["is_absent"] = 1
		entry["is_halfday"] = 1

	if not entry.get('card_out') and not entry.get('is_restday') and not entry.get('is_holiday') and not entry.get('lv_status') and not entry.get('ob_status'):
		entry["work"] = 0
		entry["late"] = 0
		entry["undertime"] = 0
		entry["is_absent"] = 1

	if entry.get('lv_status') == 1 or entry.get('suspension') == 1:
		entry["work"] = 0
		entry["late"] = 0
		entry["undertime"] = 0
		entry["is_absent"] = 0

	if entry.get('is_restday'):
		entry['late'] = 0
		entry['undertime'] = 0
		entry['is_absent'] = 0

	if not entry.get('card_out') and not entry.get('ob_status'):
		entry['overtime'] = 0
		entry['ot_list'] = ""

	if not entry.get('card_in') and not entry.get('ob_status'):
		entry['overtime'] = 0
		entry['ot_list'] = ""

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

	#if flexible
	if entry.get('is_flexible'):
		if entry.get('card_in') and entry.get('card_out'):
			#Reset Flexible values
			entry['late'], entry['undertime'], entry['work']= 0, 0 ,entry.get('worker_secs')

			if entry.get('flexible_type') == "In-Out":		
				diff = (entry.get('card_out') - entry.get('card_in')).total_seconds()  - (entry.get('break_mins') * 60)
				if diff < entry.get('worker_secs'):
					entry['undertime'] = (entry.get('worker_secs') - diff)
					entry['late'] = 0
					entry['work'] = abs(diff)
			else:
				#gete late base from flexible start time
				flex_start = entry.get('card_in')
				flex_end = entry.get('card_out')

				if entry.get('ob_status') == 1:
					if entry.get('ob_in') < entry.get('card_in'):
						flex_start = entry.get('ob_in')

					if entry.get('ob_out') > entry.get('card_out'):
						flex_end = entry.get('ob_out')

				flex = get_datetime( str(entry.get('target_date'))+" "+ str(entry.get('flex_to')) )
				if flex:
					if flex_start > ( flex + datetime.timedelta(minutes=entry.get('grace'))):
						if entry['graceperiod_late']:
							entry['late'] = ( flex_start - (flex + datetime.timedelta(minutes=entry.get('grace'))) ).total_seconds()
						else:
							entry['late'] = ( flex_start - flex ).total_seconds()
				
				#always reduce break mins
				diff = abs((flex_start - flex_end).total_seconds())  - (entry.get('break_mins') * 60)	
				
				#Get Undertime
				if diff < entry.get('worker_secs'):
					entry['undertime'] = entry.get('worker_secs') - diff
					entry['work'] = diff

		#entry['undertime'] += abs((entry.get('card_out') - entry.get('time_out')).total_seconds())		
		#if entry.get('work') < (entry.get('worker_secs')):
		#	entry['undertime'] += abs(entry.get('work') - entry.get('worker_secs'))
		#	entry['work'] += entry['late']
		#	entry['late'] = 0
		#	entry['work'] = entry.get('worker_secs') - entry['undertime']
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

	if entry.get('is_holiday'):
		entry["undertime"] = 0
		entry["late"] = 0
		entry["absent"] = 0

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
	for d in entry.get('ot_list'):
		if d.get('ot_tag'):
			entry["tags"] += d.get('ot_tag')
			
	#ut_tags
	if entry.get('suspension') == 1:
		entry["tags"] += " <span class='label label-success'> Work Suspension </span> "
	elif entry.get('suspension') == 2:
		entry["tags"] += " <span class='label label-success'> 1sthalf Work Suspension </span> "
	elif entry.get('suspension') == 3:
		entry["tags"] += " <span class='label label-success'> 2ndhalf Work Suspension </span> "

	if entry.get('linked_ut'):
		entry["tags"] += " <span class='label label-danger'> Approved Undertime </span> "
	elif entry.get('undertime') > 0:
		entry["tags"] += " <span class='label label-danger'> Undertime </span> "

	if entry.get('nightdiff') > 0:
		entry["tags"] += " <span class='label label-info'> Nightdiff </span> "

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

def default_schedule_delta_to_time(delta_obj):
	return (datetime.datetime.min + delta_obj).time()

def default_schedule_get_date(date, start, end, type, is_end):
	if is_end == 1:
		if default_schedule_delta_to_time(start) > default_schedule_delta_to_time(end):
			dt = (datetime.datetime.combine(date, default_schedule_delta_to_time(end) ) + datetime.timedelta(days=1) ).strftime('%Y-%m-%d %H:%M:%S')
		else:
			dt = datetime.datetime.combine(date, default_schedule_delta_to_time(end) ).strftime('%Y-%m-%d %H:%M:%S') 
	else:
		dt = datetime.datetime.combine(date, default_schedule_delta_to_time(start) ).strftime('%Y-%m-%d %H:%M:%S') 

	return dt

def get_default_sched_template(def_sched):
	sched_template = {}
	sched = frappe.db.sql("""SELECT * FROM `tabWork Schedule Template` WHERE `name` = %s LIMIT 1""",(def_sched), as_dict=1)

	days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
	if sched:
		for day in days:
			shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(sched[0][day]), as_dict=1)
			sched_template[day] = {
				"work_shift": shift[0]['name'],
				"work_hours": shift[0]['work_hours'],
				"break_mins": shift[0]['break_mins'],
				"time_in": shift[0]['time_in'],
				"time_out": shift[0]['time_out'],				
				"break_start": shift[0]['break_start'],
				"break_end": shift[0]['break_end'],
				"nd_start": shift[0]['nd_start'],
				"nd_end": shift[0]['nd_end'],				
				"shift_type": shift[0]['work_shift_type'],
			}

	return sched_template

def assign_default_schedule(employee, pay_from, pay_to, def_sched):
	sched_map = get_default_sched_template(def_sched)
	dates = []
	date_list = []
	schedule = []
	label = ""
	start = datetime.datetime.strptime(str(pay_from), '%Y-%m-%d')
	end = datetime.datetime.strptime(str(pay_to), '%Y-%m-%d')
	step = datetime.timedelta(days=1)
	
	while start <= end:
		date_list.append(start.date())
		start += step

	#for i in range(1, 500):
	for i in date_list:
		day = datetime.datetime.strptime(str(i), '%Y-%m-%d').strftime('%A').lower()
		info = {
			"date": i,
			"day": day,
			"work_shift": sched_map[day]['work_shift'],
			"shift_type": sched_map[day]['shift_type'],
			"work_hours": sched_map[day]['work_hours'],
			"break_mins": sched_map[day]['break_mins'],
			"datetime_in": default_schedule_get_date(i, sched_map[day]['time_in'], sched_map[day]['time_out'], sched_map[day]['shift_type'], 0),
			"datetime_out": default_schedule_get_date(i, sched_map[day]['time_in'], sched_map[day]['time_out'], sched_map[day]['shift_type'], 1),
			"break_start": default_schedule_get_date(i, sched_map[day]['break_start'], sched_map[day]['break_end'], sched_map[day]['shift_type'], 0),
			"break_end": default_schedule_get_date(i, sched_map[day]['break_start'], sched_map[day]['break_end'], sched_map[day]['shift_type'], 1),
			"nd_start": default_schedule_get_date(i, sched_map[day]['nd_start'], sched_map[day]['time_out'], sched_map[day]['shift_type'], 0),
			"nd_end": default_schedule_get_date(i, sched_map[day]['nd_start'], sched_map[day]['time_out'], sched_map[day]['shift_type'], 1),	
		}
		dates.append(info)

	company = frappe.db.get_value("Employee", employee, "company")
	exist = frappe.db.sql("""SELECT `name` FROM `tabWork Schedule` WHERE employee = %s AND target_date >= %s AND target_date <= %s """, (employee, pay_from, pay_to), as_dict=True)
	if exist:
		exist = frappe.db.sql("""DELETE FROM `tabWork Schedule` WHERE employee = %s AND target_date >= %s AND target_date <= %s """, (employee, pay_from, pay_to), as_dict=True)
						
	for d in dates:
		work_sched = frappe.new_doc("Work Schedule")
		work_sched.update({
			"employee": employee,
			"company": company,
			"target_date": d["date"],
			"work_shift": d["work_shift"],
			"shift_type": d["shift_type"],
			"work_hours": d['work_hours'],
			"break_mins": d['break_mins'],
			"datetime_in": d["datetime_in"],
			"datetime_out": d["datetime_out"],
			"break_start": d["break_start"],
			"break_end": d["break_end"],
			"nd_start": d["nd_start"],
			"nd_end": d["nd_end"],
			"is_default_schedule": 1,
		})
		work_sched.insert()

def get_schedule(employee, pay_from, pay_to):
	def_sched = frappe.db.get_value("Employee", employee, "default_schedule")
	date_list = []
	start = datetime.datetime.strptime(str(pay_from), '%Y-%m-%d')
	end = datetime.datetime.strptime(str(pay_to), '%Y-%m-%d')
	step = datetime.timedelta(days=1)
	
	if def_sched:
		while start <= end:
			date_list.append(start.date())
			start += step

		for d in date_list:
			sched = frappe.db.sql("""SELECT employee, company, work_shift, work_hours, break_mins, target_date, shift_type, 
				datetime_in, datetime_out, break_start, break_end, nd_start, nd_end, o_time_in, o_break_in, o_break_out, o_time_out
				FROM `tabWork Schedule` 
				WHERE employee = %(employee)s AND target_date = %(target_date)s """,{
					"employee": employee,
					"target_date": d
				}, as_dict=True)

			if not sched:
				assign_default_schedule(employee, d, d, def_sched)
		
	schedule = frappe.db.sql("""SELECT employee, company, work_shift, work_hours, break_mins, target_date, shift_type, 
		datetime_in, datetime_out, break_start, break_end, nd_start, nd_end, o_time_in, o_break_in, o_break_out, o_time_out
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
			is_flexible, setup_preshift, setup_postshift, flex_from, flex_to, 
			end_preshift, end_postshift, graceperiod_late, straight_ot, flexible_type, nd_end, nd_start
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
			"setup_preshift": d.setup_preshift,
			"setup_postshift": d.setup_postshift,
			"flex_from": d.flex_from,
			"flex_to": d.flex_to,
			"end_preshift": d.end_preshift,
			"end_postshift": d.end_postshift,
			"graceperiod_late": d.graceperiod_late,
			"straight_ot": d.straight_ot,
			"flexible_type": d.flexible_type,
			"nd_start": d.nd_start,
			"nd_end": d.nd_end
		}

	return shift_map

def get_holiday_list(company, location, from_date, to_date):
	holidays = frappe.db.sql("""SELECT holiday_name, holiday_date, is_special FROM `tabHoliday` 
		WHERE company = %s AND location = %s AND holiday_date >= %s AND holiday_date <= %s
		ORDER BY holiday_date ASC""",(company, location, from_date, to_date), as_dict=True)

	return holidays

def get_leave_list(employee, from_date, to_date, approval_cutoff, adjustment):
	by_adjustment = "" if adjustment == 1 else "AND approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' "

	leave_list = frappe.db.sql("""SELECT L.`name`, L.employee, L.leave_type, LA.leave_date, LA.is_half_day, LA.is_second_half, LA.is_holiday, LA.is_excluded, L.is_lwop
		FROM `tabLeave Application Table` LA
		INNER JOIN `tabLeave Application` L ON L.`name` = LA.parent
		WHERE L.employee = %s AND LA.leave_date >= %s AND LA.leave_date <= %s {by_adjustment} AND L.docstatus = '1' 
		ORDER BY LA.leave_date ASC """.format( by_adjustment=by_adjustment ), (employee, from_date, to_date), as_dict=1)

	return leave_list

def get_ob_list(employee, from_date, to_date, approval_cutoff, adjustment):
	by_adjustment = "" if adjustment == 1 else "AND approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' "

	ob_apps = frappe.db.sql("""SELECT OBA.`name`, OBAT.target_date, OBAT.from_time, OBAT.to_time, OBAT.hrs, OBAT.is_holiday, OBAT.is_excluded 
		FROM `tabOfficial Business Application Table` OBAT
		INNER JOIN `tabOfficial Business Application` OBA  ON OBAT.parent = OBA.`name`
		WHERE OBA.employee = %s AND OBA.workflow_state = 'Approved' AND OBAT.target_date >= %s 
		AND OBAT.target_date <= %s AND OBAT.is_excluded = 0 {by_adjustment} """.format( by_adjustment=by_adjustment ), (employee, from_date, to_date), as_dict=1)

	return ob_apps

def get_ot_list(employee, from_date, to_date, approval_cutoff, adjustment):
	by_adjustment = "" if adjustment == 1 else "AND approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' "

	ot_apps = frappe.db.sql("""SELECT `name`, total_hrs, break_hrs, target_date, from_date, to_date, from_time, to_time FROM `tabOvertime Application` 
		WHERE workflow_state = 'Approved' AND employee = %s AND target_date >= %s 
		AND target_date <= %s {by_adjustment} """.format( by_adjustment=by_adjustment ), (employee, from_date, to_date), as_dict=1)
	return ot_apps

def get_ut_list(employee, from_date, to_date, approval_cutoff, adjustment):
	by_adjustment = "" if adjustment == 1 else "AND approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' "

	ut_apps = frappe.db.sql("""SELECT `name`, from_time, to_time, from_date FROM `tabUndertime Application` 
		WHERE workflow_state = 'Approved' AND employee = %s AND from_date >= %s 
		AND from_date <= %s {by_adjustment} """.format( by_adjustment=by_adjustment ), (employee, from_date, to_date), as_dict=1)

	return ut_apps

def get_cto_list(employee, from_date, to_date, approval_cutoff, adjustment):
	by_adjustment = "" if adjustment == 1 else "AND approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' "

	cto_apps = frappe.db.sql("""SELECT `name`, use_fromtime, use_totime,  from_date FROM `tabCompensatory Time Off` 
		WHERE workflow_state = 'Approved' AND employee = %s AND from_date >= %s AND from_date <= %s
		AND `type` = 'Use' {by_adjustment} """.format( by_adjustment=by_adjustment ), (employee, from_date, to_date), as_dict=1)
	
	return cto_apps

def get_ext_list(employee, from_date, to_date, approval_cutoff, adjustment):
	by_adjustment = "" if adjustment == 1 else "AND approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' "

	ext_apps = frappe.db.sql("""SELECT `name`, `date`, from_time, to_time, `type` FROM `tabExcuse Tardiness Application` 
		WHERE workflow_state = 'Approved' AND employee = %s AND `date` >= %s 
		AND `date` <= %s {by_adjustment} """.format( by_adjustment=by_adjustment ), (employee, from_date, to_date), as_dict=1)
	
	return ext_apps

def get_ws_list(from_date, to_date, approval_cutoff, adjustment):
	by_adjustment = "" if adjustment == 1 else "AND approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' "	

	ws_apps = frappe.db.sql(""" SELECT apply_to, apply_value, target_date, suspension_start, suspension_end FROM `tabWork Suspension` WS 
		INNER JOIN `tabWork Suspension Dates` WSD ON WSD.parent = WS.`name`
		INNER JOIN `tabWork Suspension Apply` WSA ON WSA.parent = WS.`name` WHERE target_date >= %s 
		AND target_date <= %s {by_adjustment} """.format( by_adjustment=by_adjustment ), (from_date, to_date), as_dict=1)

	return ws_apps

def get_suspension_map(from_date, to_date):
	suspension_map = {}
	suspensions = frappe.db.sql(""" SELECT apply_to, apply_value, target_date, suspension_start, suspension_end FROM `tabWork Suspension` WS 
		INNER JOIN `tabWork Suspension Dates` WSD ON WSD.parent = WS.`name`
		INNER JOIN `tabWork Suspension Apply` WSA ON WSA.parent = WS.`name` WHERE target_date >= %s AND target_date <= %s AND WS.docstatus = 1 """, (from_date, to_date), as_dict=1)
	
	if suspensions:
		for d in suspensions:
			suspension_name = ""+cstr(d.apply_to)+"_"+cstr(d.apply_value)+"_"+cstr(d.target_date)+""
			suspension_map[suspension_name] = {
				"apply_to": d.apply_to,
				"apply_value": d.apply_value,
				"suspension_date": d.target_date,
				"suspension_start": d.suspension_start,
				"suspension_end": d.suspension_end,
			}

	return suspension_map

def get_suspension(emp, suspension_map, entry):
	if suspension_map:
		start, end = "", ""
		company = "Company_"+cstr(emp.company)+"_"+cstr(entry.get('target_date'))+""
		location = "Location_"+cstr(emp.location)+"_"+cstr(entry.get('target_date'))+""
		department = "Department_"+cstr(emp.department)+"_"+cstr(entry.get('target_date'))+""
		if company in suspension_map:
			start = suspension_map[company]['suspension_start']
			end = suspension_map[company]['suspension_end']

		if location in suspension_map:
			start = suspension_map[location]['suspension_start']
			end = suspension_map[location]['suspension_end']
			
		if department in suspension_map:
			start = suspension_map[department]['suspension_start']
			end = suspension_map[department]['suspension_end']

		if start and end:
			if start < end:
				entry['suspension_start'] = get_datetime( str(entry.get('target_date') )+" "+ str(start) )
				entry['suspension_end'] = get_datetime( str(entry.get('target_date') )+" "+ str(end) )
			elif start > end:
				entry['suspension_start'] = get_datetime( str(entry.get('target_date') )+" "+ str(start) )
				entry['suspension_end'] = get_datetime( str( add_days(entry.get('target_date'), 1) )+" "+ str(end) )

		if entry['suspension_start'] and entry['suspension_end']:
			entry['suspension'] = 1			
			if entry['suspension_start'] >= entry['break_end']:
				entry['suspension'] = 3
			else:	
				if entry['suspension_end'] <= entry['break_end']:
					entry['suspension'] = 2


	return entry

def get_card_within(pre_shift, max_preshift, post_shift, max_postshift, timecard_list):
	cards_in = []
	cards_out = []
	#frappe.throw(_(timecard_list))
	for tc in timecard_list:
		if pre_shift <= tc.card_datetime <= max_preshift and (tc.card_type == 0 or tc.card_type == 2):
			cards_in.append({
				"card_name":tc.name,
				"card_time":tc.time,
				"card_datetime": tc.card_datetime,
				"card_type": tc.card_type
			})				

		if post_shift <= tc.card_datetime <= max_postshift and (tc.card_type == 1 or tc.card_type == 3):
			cards_out.append({
				"card_name":tc.name,
				"card_time":tc.time,
				"card_datetime": tc.card_datetime,
				"card_type": tc.card_type
			})

	return cards_in, cards_out

def get_sorted_card(entry, cards_in, cards_out):
	sorted_in = sorted(cards_in, key=lambda k: k['card_datetime'])
	sorted_out = sorted(cards_out, key=lambda k: k['card_datetime'])
	
	for card in sorted_in:
		if card['card_type'] == 0:
			if entry['card_in'] == "":
				entry['card_in'] = card['card_datetime']
		elif card['card_type'] == 2:
			if entry['break_out'] == "":
				entry['break_out'] = card['card_datetime']
 	
 	for card in sorted_out:
		if card['card_type'] == 1:
			entry['card_out'] = card['card_datetime']
		elif card['card_type'] == 3:
			entry['break_in'] = card['card_datetime']

 	return entry

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

def insert_overtime(entry):
	for d in entry.get('ot_list'):
		ot = frappe.new_doc("Overtime")
		ot.update({
			"employee": d.get('employee'),
			"target_date": d.get('target_date'),
			"ot_code": d.get('ot_code'),	
			"hrs": d.get('ot_hrs'),
			"linked_ot": d.get('linked_ot'),
		})
		ot.insert()

	entry['ot_list'] = 0.0

def get_defaults(emp, sched, shift_map):
	entry = {
		#employe settings
		"employee": emp.name,
		"company": emp.company,
		"location": emp.location,
		"department": emp.department,
		"worker_hrs": emp.no_hours,
		"worker_secs": (emp.no_hours * 60) * 60,
		"is_attendance_base": emp.is_attendance_base,
		#schedule settings
		"target_date": getdate(sched.datetime_in),
		"work_shift": sched.work_shift,
		"pre_shift": add_to_date(sched.datetime_in, hours= (0 - shift_map[sched.work_shift]['setup_preshift']) ),
		"end_preshift": add_to_date(sched.datetime_in, hours= shift_map[sched.work_shift]['end_preshift'] ),
		"post_shift": add_to_date(sched.datetime_out, hours= (0 - shift_map[sched.work_shift]['setup_postshift']) ),
		"end_postshift": add_to_date(sched.datetime_out, hours=shift_map[sched.work_shift]['end_postshift'] ),	
		"time_in": sched.datetime_in,
		"time_out": sched.datetime_out,
		"break_start": sched.break_start,
		"break_end": sched.break_end,
		"nd_start": shift_map[sched.work_shift]['nd_start'],
		"nd_end": shift_map[sched.work_shift]['nd_end'],
		#shift policy
		"work_hours": shift_map[sched.work_shift]['work_hours'],
		"break_mins": sched.break_mins,
		"grace": shift_map[sched.work_shift]['grace_period'],
		"b_grace": shift_map[sched.work_shift]['b_grace_period'],
		"is_flexible": shift_map[sched.work_shift]['is_flexible'],
		"flex_from": shift_map[sched.work_shift]['flex_from'],
		"flex_to": shift_map[sched.work_shift]['flex_to'],		
		"is_restday": shift_map[sched.work_shift]['is_restday'],
		#general policy
		"is_processed": 0,
		#timecard data
		"card_in": "",
		"card_out": "",
		"override_in": sched.o_time_in,
		"override_out": sched.o_time_out,			
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
		"ot_list": "",
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
		#SUSPENSION
		"suspension": 0,
		"suspension_start": "",
		"suspension_end": "",
		#POLICIES
		"graceperiod_late": shift_map[sched.work_shift]['graceperiod_late'],
		"straight_ot": shift_map[sched.work_shift]['straight_ot'],
		"flexible_type": shift_map[sched.work_shift]['flexible_type'],
		"ot_start_delay": flt(frappe.db.get_single_value('Timekeeping Settings', 'ot_start_delay'), 8),
		"ot_interval": flt(frappe.db.get_single_value('Timekeeping Settings', 'ot_interval'), 8),
		"late_interval": flt(frappe.db.get_single_value('Timekeeping Settings', 'late_interval'), 8),
	}
	return entry

