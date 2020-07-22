from __future__ import unicode_literals
import frappe, datetime, math
from frappe.utils import cint, cstr, flt, nowdate, add_days, getdate, fmt_money, get_datetime, add_to_date
from frappe import _
from datetime import timedelta, date

def get_attendance(entry, overrides, leaves, holidays, obs, ots, uts, ext, cto, wss, dtrp):
	if dtrp:
		for dt in dtrp:
			if dt['target_date'] == entry['target_date']:
				entry['is_dtrp'] = 1
				if dt['name'] not in entry['dtrp_links']:
					entry['dtrp_links'].append(dt['name'])

	for over in overrides:
		if over['target_date'] == entry['target_date']:
			if over.get("time_in"):
				entry['card_in'] = get_datetime(str(over.get("time_in")))

			if over.get("time_out"):
				entry['card_out'] = get_datetime(str(over.get("time_out")))

	#Format Datetime for realtime shift
	entry['time_in'] = get_datetime( str(entry.get('target_date'))+" "+ str(entry.get('time_in')) )
	entry['time_out'] = get_datetime( str(entry.get('target_date'))+" "+ str(entry.get('time_out')) )
	entry['break_start'] = get_datetime( str(entry.get('target_date'))+" "+ str(entry.get('break_start')) )
	entry['break_end'] = get_datetime( str(entry.get('target_date'))+" "+ str(entry.get('break_end')) )
	if entry.get('time_in') > entry.get('time_out'):
		entry['time_out'] = add_days(entry.get('time_out'), 1)

	#check Break Out and break IN
	if entry.get('break_start') < entry.get('time_in'):
		entry['break_start'] = add_days(entry.get('break_start'), 1) 

	if entry.get('break_end') < entry.get('time_in'):
		entry['break_end'] = add_days(entry.get('break_end'), 1)

	if obs:
		for ob in obs:
			if ob['target_date'] == entry['target_date']:
				ob_in = get_datetime( str(ob.date)+" "+ str(ob.from_time) )
				ob_out = get_datetime( str(ob.to_date)+" "+ str(ob.to_time) )
				if ob_out < ob_in:
					ob_out = get_datetime( str(add_days(ob.date, 1))+" "+ str(ob.to_time) )

				if not (ob_in <= entry.get('time_in') and ob_out <= entry.get('time_in')):
					entry['ob_links'].append(ob.name) 
					entry['linked_ob'] = ob.name
					entry['is_ob'], entry['ob_status'], entry['ob_stat'], entry["is_absent"], entry['is_lwop'] = 1, 1, 1, 0, 0

					if not entry['ob_in']:
						entry['ob_in'] = ob_in
					elif entry['ob_in'] and ob_in < entry['ob_in']:
						entry['ob_in'] = ob_in

					if not entry['ob_out']:
						entry['ob_out'] = ob_out
					elif entry['ob_out'] and ob_out > entry['ob_out']:
						entry['ob_out'] = ob_out

					if entry.get('ob_in') >= entry.get('break_start') and entry.get('ob_in') <= entry.get('time_out') : #if OB is in second half
						entry['ob_stat'] = 3
					else: #if OB is in first half
						if entry.get('ob_out') <= entry.get('break_end'):
							entry['ob_stat'] = 2
	
				else:
					if (ob_in < entry.get('time_in') and ob_out <= entry.get('time_in')):
						entry['ob_links'].append(ob.name)
						early_ob_in = ob_in
						early_ob_out = ob_out

						if early_ob_in > entry.get('time_in'):
							early_ob_in = entry.get('time_in')

						if early_ob_out > entry.get('time_in'):
							early_ob_out = entry.get('time_in')

						entry['early_ob'] = 1
						entry['early_ob_in'] = early_ob_in
						entry['early_ob_out'] = early_ob_out

	if uts:
		for ut in uts:
			if ut['from_date'] == entry['target_date']:
				entry['ut_links'].append(ut.name)
				entry['ut_from'] = get_datetime( str(ut.from_date)+" "+ str(ut.from_time))
				entry['ut_to'] = get_datetime(str(ut.to_date) +" "+str(ut.to_time))
				entry['linked_ut'] = ut.name

	if ext:
		for et in ext:
			if et['date'] == entry['target_date']:
				et_start = get_datetime( str(et['date']) +" "+ str(et.from_time))
				et_end = get_datetime( str(et['date']) +" "+ str(et.to_time) )
				entry['ex_tardiness'].append({'type': et['type'], 'from_time': et_start, 'to_time': et_end})
				entry['ext_links'].append(et.name)

	if holidays:
		dbh = 0
		for h in holidays:
			if getdate(h['holiday_date']) == getdate(entry['target_date']):
				if h.get('location'):
					if entry.get('location') == h.get('location'):
						dbh += 1
						entry["is_absent"] = 0
						entry['is_lwop'] = 0
						entry["undertime"] = 0
						entry["late"] = 0
						entry['holiday_name'] = h['holiday_name']
						entry['is_holiday'] = 1
						if h['is_special'] == 1:
							entry['is_sp_holiday'] = 1
				else:		
					dbh += 1
					entry["is_absent"] = 0
					entry['is_lwop'] = 0
					entry["undertime"] = 0
					entry["late"] = 0
					entry['holiday_name'] = h['holiday_name']
					entry['is_holiday'] = 1
					if h['is_special'] == 1:
						entry['is_sp_holiday'] = 1

		if dbh >= 2:
			entry['is_db_holiday'] = 1

	#leaves	
	lv_whole = {"half_lv": 0, "half_lwop": 0}
	for l in leaves:
		if l['leave_date'] == entry['target_date']:
			entry['lv_links'].append(l.name) 
			if l['is_excluded'] != 1:
				entry['leave_name'] += (" "+l.leave_type+"")
				entry['linked_leave'] = l.name
				entry["lv_status"] = 1
				if not entry['card_in'] or not entry['card_out']:
					entry['work'] = (entry.get('work_hours') * 60) * 60

				if l.is_lwop == 1:
					entry['is_lwop'] = 1
				
				if l.is_half_day and not l.is_second_half:
					entry["lv_status"] = 2
					if l.is_lwop != 1:
						lv_whole["half_lv"] += 1
						entry["pd_lv_status"] = 2
					else:
						lv_whole["half_lwop"] += 1
						entry["lwop_status"] = 2

				if l.is_second_half:
					entry["lv_status"] = 3
					if l.is_lwop != 1:
						lv_whole["half_lv"] += 1
						entry["pd_lv_status"] = 3
					else:
						lv_whole["half_lwop"] += 1
						entry["lwop_status"] = 3

				elif l.is_half_day:
					entry["lv_status"] = 2

		if lv_whole["half_lv"] > 0 or lv_whole["half_lwop"] > 0:
			if lv_whole["half_lv"] > 1:
				entry["lv_status"] = 1
			if lv_whole["half_lwop"] > 1:
				entry["lv_status"] = 1

	for ws in wss:
		if getdate(ws.suspension_date) == getdate(entry['target_date']):	
			if ws.suspension_start and ws.suspension_end:
				entry['suspension'] = 1
				if ws.suspension_start  >= entry['break_end']:
					entry['suspension'] = 3
				else:	
					if ws.suspension_end <= entry['break_end']:
						entry['suspension'] = 2

	entry['late_list'] = []
	entry['ut_list'] = []
	entry['cto_list'] = []
	get_late(entry)
	get_overtime(entry, ots)
	get_undertime(entry)
	get_ndiff(entry)
	get_absent(entry)
	get_work(entry)
	get_flexible(entry, obs)
	get_final_processing(entry)
	get_cto(entry, cto)
	get_tags(entry)
	get_links(entry)

def get_work(entry):
	#if (not entry.get('is_restday') or not entry.get('is_holiday')) and entry['card_in'] and entry['card_out']:
	#	entry['work'] = (entry.get('work_hours') * 60) * 60
	#	if entry["lv_status"] == 3:
	#		entry['work'] = entry['work'] / 2
		
	#	elif entry["lv_status"] == 2:
	#		entry['work'] = entry['work'] / 2

	#	elif entry["lv_status"] == 1:
	#		entry['work'] = 0

	#	else:
	#		if entry["is_halfday"] == 1:
	#			entry['work'] = entry['work'] / 2

	#elif entry.get('ob_stat') == 1:
	#	entry['work'] = (entry.get('work_hours') * 60) * 60
	#	if entry["is_halfday"] == 1:
	#		entry['work'] = entry['work'] / 2

	#if entry.get('ob_stat') > 1 and not entry['card_in'] and not entry['card_out']:
	#	if not entry["lv_status"]:
	#		entry['work'] = (entry.get('work_hours') * 60) * 60
	#		entry['work'] = entry['work'] / 2

	if (not entry.get('is_restday') and not entry.get('is_holiday')):# and entry["lv_status"] == 1 and not entry['is_lwop'] and not entry['card_in'] and not entry['card_out']:
		entry['work'] = (entry.get('work_hours') * 60) * 60

		if entry["lv_status"] > 1:
	
			if entry["lv_status"] == 2:
				entry['work'] = abs((entry.get('time_out') - entry.get('break_end')).total_seconds())
			if entry["lv_status"] == 3:
				entry['work'] = abs((entry.get('time_in') - entry.get('break_start')).total_seconds())
	
		elif entry["lv_status"] == 1:
			entry['work'] = 0

	else:
		if entry.get('card_in') and entry.get('card_out'):
			entry['work'] = (entry.get('work_hours') * 60) * 60
		else:
			if entry.get('ob_stat') == 1:
				entry['work'] = (entry.get('work_hours') * 60) * 60
				if entry["is_halfday"] == 1:
					entry['work'] = entry['work'] / 2
			if entry.get('ob_stat') > 1 and not entry['card_in'] and not entry['card_out']:
				if not entry["lv_status"]:
					entry['work'] = (entry.get('work_hours') * 60) * 60
					entry['work'] = entry['work'] / 2

	return entry

def get_overtime(entry, ot_apps):
	ot_list = []
	work_shift = []
	ot_map = get_overtime_map()
	total_ot, total_brk, total_ot_n, total_ot_nd, total_ot_ex = 0.0, 0.0, 0.0, 0.0, 0.0
	otho_total, otho_used = 0.00, 0.00
	nd_start = None
	nd_end = None
	nd_early_start = None
	strict_logs = frappe.db.get_single_value('Timekeeping Settings', 'ot_strict_logs')
	to_hrs, from_hrs, break_mins = 0, 0, 0
	entry["ot_card_in"], entry["ot_card_out"], entry["ot_ob_in"], entry["ot_ob_out"] = "","","",""

	#Get Nigthdiff Setup
	if entry.get('nd_start') and entry.get('nd_end'):
		nd_start = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_start')) )
		nd_end = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_end')) )
		if entry.get('nd_start') > entry.get('nd_end'):
			nd_end = get_datetime( str( add_days(entry.get('target_date'), 1) ) +" "+ str(entry.get('nd_end')) )

		nd_early_start = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_end')) )

	if ot_apps:
		counter = 0
		for d in ot_apps:
			counter+=1
			ot_int_start = None
			per_time_with_ot = []
			is_break_deducted = 0
			ot_hrs, ot_nd, ot_normal, org_ot_normal = 0, 0, 0, 0
			ot_log_list, ots = [], []
			log_used = 0

			if getdate(d.get('target_date')) == entry.get('target_date'):
				entry['ot_links'].append(d.get("name")) 
				linked_ot = d.name
				ot_in = get_datetime( str(d.from_date) +" "+ str(d.from_time))
				ot_out = get_datetime( str(d.to_date) +" "+ str(d.to_time) )
				org_ot_in = get_datetime( str(d.from_date) +" "+ str(d.from_time) )
				org_ot_out = get_datetime( str(d.to_date) +" "+ str(d.to_time) )
				is_saturday = 1 if getdate(entry.get('target_date')).weekday() == 5 else 0
				is_sunday = 1 if getdate(entry.get('target_date')).weekday() == 6 else 0
				is_db_holiday = entry.get('is_db_holiday')

				#get Card Out if Straight OT
				if ot_out and entry.get('straight_ot'):
					if entry['card_out']:
						if ot_out > entry['card_out']:
							entry['card_out'] = ot_out
					else: 
						entry['card_out'] = ot_out

				#get OT Start based from interval
				if entry['ot_interval']:
					ot_int_start = add_to_date(ot_in, hours=(entry.get('ot_start_delay') / 60) )
				if entry.get('ot_start_delay'):
					ot_delay_start = add_to_date(entry.get('time_out'), hours=(entry.get('ot_start_delay') / 60) )
					if ot_delay_start > ot_in:
						ot_in = ot_delay_start

				
				#get OT Start Deduct Late
				if entry.get('ot_deduct_late') and not entry.get('is_flexible'):
					if entry.get('is_restday') < 1:
						if entry.get('is_holiday'):
							if entry.get('ot_dedlt_ho'):
								ot_in = add_to_date(ot_in, hours=( entry.get('late') / 60 / 60 ) )
						else:
							ot_in = add_to_date(ot_in, hours=( entry.get('late') / 60 / 60 ))

				#Always follow whichever is lower between card_out and ot_out
				if entry.get('ot_strict_logs'):
					if ot_in < entry.get('time_in') and ot_out >  entry.get('time_out') and not entry.get('is_restday') and not entry.get('is_holiday'):
						ots = [{'ot_in': ot_in, 'ot_out': entry.get('time_in')}, {'ot_in': entry.get('time_out'), 'ot_out': ot_out}]
					
					else:
						ots = [{'ot_in': ot_in, 'ot_out': ot_out}]

					start, end = None, None
					bound = None

					if (entry['card_in'] and not entry['card_out']) or (entry['card_out'] and not entry['card_in']):
						if entry['card_in']:
							start = entry['card_in']

							if entry['early_ob'] == 1:
								if not (ot_in >= entry.get('early_ob_out') or ot_out <= entry.get('early_ob_in')):
									end = entry.get('early_ob_out')
									if entry.get('early_ob_in') < entry.get('card_in'):
										start =  entry.get('early_ob_in')
									

							if entry.get('ob_in'):
								if not (ot_in >= entry.get('ob_out') or ot_out <= entry.get('ob_in')):
									if start and end:
										if not (entry.get('ob_in') >= end or entry.get('ob_out') <= start):
											if entry.get('ob_in') < get_datetime(start):
												start = entry.get('ob_in') 
											if entry.get('ob_out') > end:
												end = entry.get('ob_out') 
										else:
											ot_log_list.append({'start': entry.get('ob_in'), 'end': entry.get('ob_out')})
									else:
										end = entry.get('ob_out')
										if entry.get('ob_in') < entry.get('card_in'):
											start = entry['ob_in'] 
									

						if entry['card_out']:
							end = entry['card_out']
							
							if entry['ob_in']:
								if not (ot_in >= entry.get('ob_out') or ot_out <= entry.get('ob_in')):
									start = entry.get('ob_in')
									if entry.get('ob_out') > entry.get('card_out'):
										end =  entry.get('ob_out')

							if entry.get('early_ob'):
								if not (ot_in >= entry.get('early_ob_out') or ot_out <= entry.get('early_ob_in')):
									if start and end:
										if not (entry.get('early_ob_in') >= end or entry.get('early_ob_out') <= get_datetime(start)):
											if entry.get('early_ob_in') < get_datetime(start):
												start = entry.get('ob_in') 
											if entry.get('early_ob_out') > end:
												end = entry.get('ob_out') 
										else:
											ot_log_list.append({'start': entry.get('early_ob_in'), 'end': entry.get('early_ob_out')})
									else:
										start = entry.get('early_ob_in')
										if entry.get('early_ob_out') > entry.get('card_out'):
											end = entry['early_ob_out'] 

					else:
						if entry.get('card_in') and entry.get('card_out'):
							if not (ot_in >= entry.get('card_out') or ot_out <= entry.get('card_in')):
								start, end = entry.get('card_in'), entry.get('card_out')
								
						if entry['early_ob'] == 1:
							if not (ot_in >= entry.get('early_ob_out') or ot_out <= entry.get('early_ob_in')):
								if start:
									if not (get_datetime(start) >= get_datetime(entry['early_ob_out']) and get_datetime(end) <= get_datetime(entry['early_ob_in'])):
										if entry.get('early_ob_in') < get_datetime(start):
											start = entry.get('early_ob_in')
										if entry.get('early_ob_out') > get_datetime(end):
											end = entry.get('early_ob_out')
									else:
										ot_log_list.append({'start': entry.get('early_ob_in'), 'end': entry.get('early_ob_out')})
								else:
									start, end = entry.get('early_ob_in'), entry.get('early_ob_out')

						if entry.get('ob_in'):
							if not (ot_in >= entry.get('ob_out') or ot_out <= entry.get('ob_in')):
								if start:
									if not (get_datetime(start) >= entry.get('ob_out') and get_datetime(end) <= entry.get('ob_in')):
										if entry.get('ob_in') < get_datetime(start):
											start = entry.get('ob_in')
										if entry.get('ob_out') > get_datetime(end):
											end = entry.get('ob_out')
									else:
										ot_log_list.append({'start': entry.get('ob_in'), 'end': entry.get('ob_out')})
								else:
									start, end = entry.get('ob_in'), entry.get('ob_out')

					if start and end:
						ot_log_list.append({'start': start, 'end': end})
					for o in ots:
						if o.get('ot_in') < entry.get('time_in'):
							bound = entry.get('time_in')
						else:
							bound = entry.get('time_out')
							if not entry.get('is_restday') and not entry.get('is_holiday'):
								if o.get('ot_in') < bound <= o.get('ot_out'):
									o['ot_in'] = bound
								if o.get('ot_out') <= bound:
									 start, end = None, None

						for ot in ot_log_list:
							ot_start, ot_end = get_ot(o.get('ot_in'), o.get('ot_out'), ot.get('start'), ot.get('end'), bound, entry['is_restday'], entry['is_holiday'])
							if ot_start != ot_end:

								per_time_with_ot.append({"ot_in": ot_start, "ot_out": ot_end})

				if not per_time_with_ot and entry.get('ot_strict_logs'):
					if ot_in and ot_out:
						per_time_with_ot.append({
							"ot_in": ot_in,
						 	"ot_out": ot_in
						})

				if not entry.get('ot_strict_logs'):
					if ot_in and ot_out:
						per_time_with_ot.append({
							"ot_in": ot_in,
						 	"ot_out": ot_out
						})

				for o in per_time_with_ot:
					ot_in = o['ot_in']
					ot_out = o['ot_out']

					#get Max Holiday OT per day
					if entry.get('is_holiday') == 1:
						if entry.get('max_holiday_ot'):
							otho_maxdiff = (ot_out - ot_in).total_seconds() / 60.0

							if otho_total < entry.get('max_holiday_ot'):
								if (otho_total + otho_maxdiff) <= entry.get('max_holiday_ot'):
									otho_total += otho_maxdiff
								else:
									otho_total = entry.get('max_holiday_ot')
 	
								otho_out = ot_in + datetime.timedelta(minutes=otho_total-otho_used)
								if otho_out <= ot_out:
									ot_out = otho_out
								otho_used += otho_total
							else:
								ot_out = ot_in

					# OT IN should not be greater than OT Out
					if get_datetime(ot_in) > get_datetime(ot_out):
						ot_in = ot_out

					#Get Normal OT before ND and Should also consider early ND OT
					ot_normal += abs((get_datetime(ot_in) - get_datetime(ot_out)).total_seconds())

					#Get ND OT Start and End
					ot_nd_start = None #Start Time of OT ND computation
					ot_nd_end = None #End Time of OT ND computation
					if nd_start and nd_end:
						if get_datetime(ot_out) > get_datetime(nd_start):
							# GET ND OT START
							if ot_in >= nd_start:
								ot_nd_start = ot_in
								# if OT in is greater than ot out set to None
								if ot_in > ot_out:
									ot_nd_start = None
							elif ot_in < nd_start: #if OT IN is beyond ND, limit to ND START
								ot_nd_start = nd_start
	
							# GET ND OT END
							if get_datetime(ot_out) <= get_datetime(nd_end): #if OT OUT is inside ND
								ot_nd_end = ot_out
								# if OT OUT is less than OT IN set to none
								if get_datetime(ot_out) < get_datetime(nd_start):
									ot_nd_end = None
							elif get_datetime(ot_out) > get_datetime(nd_end):  #if OT OUT is beyond ND, limit to ND END
								ot_nd_end = nd_end
	
					#Get ND OT and Calculate ND OT From Start to End
					if ot_nd_start and ot_nd_end and ot_nd_start < ot_nd_end:
						ot_nd = abs((ot_nd_start - ot_nd_end).total_seconds())
	
					if nd_early_start:
						#Get early ND OT
						if ot_in < nd_early_start:
							if ot_out > nd_early_start:
								ot_nd = abs((ot_in - nd_early_start).total_seconds())
							else:
								ot_nd = abs((get_datetime(ot_in) - get_datetime(ot_out)).total_seconds())


					if d.break_hrs:
						to_hrs, from_hrs, break_mins = frappe.db.get_value("Overtime Application", d['name'], ["to_hrs", "from_hrs", "break_mins"])
						if is_break_deducted != 1:
							if flt(from_hrs, 8) * 60 * 60 <= ot_normal <= flt(to_hrs, 8) * 60 * 60:
								total_brk += flt(break_mins, 8) * 60
							if flt(from_hrs, 8) * 60 * 60 <= ot_nd <= flt(to_hrs, 8) * 60 * 60:
								ot_nd -= flt(break_mins, 8) * 60
							is_break_deducted = 1

					total_ot += ot_normal
					total_ot_nd += ot_nd
					
		# REDUCE BREAK HRS ON REGULAR OT
		if total_brk:
			total_ot -= total_brk

		# GET REGULAR OT
		if total_ot > 0:
			total_ot_n = total_ot

			if total_ot_n > 28800:
				total_ot_n = 28800

			if entry.get('ot_interval'):
				total_ot_n = (entry.get('ot_interval') * 60) * int(total_ot_n / (entry.get('ot_interval') * 60))

			ot_normal_code = [entry.get('is_restday'), entry.get('is_holiday'), entry.get('is_sp_holiday'), is_db_holiday, is_sunday, is_saturday, 0, 0]
			ot_normal_code = ''.join(str(x) for x in ot_normal_code)
			ot_list.append({
				"employee": entry.get('employee'),
				"target_date": entry.get('target_date'),
				"ot_type": "OT_NORMAL",
				"ot_code": ot_normal_code,
				"ot_hrs": total_ot_n / 60 / 60,
				#"linked_ot": d.name,
				"ot_tag": "",
			})
			entry['overtime'] = total_ot_n

		# GET NIGHTDIFF OT
		if total_ot_nd > 0:
			if entry.get('ot_interval'):
				total_ot_nd = (entry.get('ot_interval') * 60) * int(total_ot_nd / (entry.get('ot_interval') * 60))
			ot_nd_code = [entry.get('is_restday'), entry.get('is_holiday'), entry.get('is_sp_holiday'), is_db_holiday, is_sunday, is_saturday, 0, 1]
			ot_nd_code = ''.join(str(x) for x in ot_nd_code)
			ot_list.append({
				"employee": entry.get('employee'),
				"target_date": entry.get('target_date'),
				"ot_type": "OT_ND",
				"ot_code": ot_nd_code,
				"ot_hrs": total_ot_nd  / 60 / 60,
				#"linked_ot": d.name,
				"ot_tag": "",
			})
			entry['overtime_nd'] = total_ot_nd

		# GET EXCESS OT
		if total_ot > 28800:
			ot_ex = (total_ot - 28800)
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
				#"linked_ot": d.name,
				"ot_tag": "",
			})
			entry['overtime_ex'] = ot_ex

		# CREATE OT TAGS
		for l in ot_list:
			overtime_type = l.get('ot_code')
			if overtime_type in ot_map:
				l["ot_tag"] += " <span class='label label-success'>"+ot_map[overtime_type]['name']+" "+cstr(l.get('ot_hrs')) +" Hrs </span> "
			else:
				l["ot_tag"] += " <span class='label label-success'>OT-"+overtime_type+"</span> "	

		entry['ot_list'] = ot_list
	return entry

def get_ot(ot_in=None ,ot_out=None, start=None, end=None, bound=None, restday=None, holiday=None):

	if holiday or restday:
		bound = ot_in
	if start:
		#After shift ot
		if get_datetime(bound) <= get_datetime(ot_in):

			if not (get_datetime(ot_in) >= get_datetime(end)) and not (get_datetime(ot_out) <= get_datetime(start)):
				if get_datetime(start) < get_datetime(bound):
					start = bound
				if get_datetime(ot_in) <= get_datetime(bound):
					ot_in = bound
				if get_datetime(start) > ot_in:
					ot_in = start
				if get_datetime(end) < ot_out:
					ot_out = end

			else:
				ot_out = ot_in

		#Early OT
		if get_datetime(bound) > get_datetime(ot_in):
			
			if not get_datetime(ot_in) >= get_datetime(end) and not get_datetime(ot_out) <= get_datetime(start):
				if get_datetime(end) > get_datetime(bound):
					end = bound
				if get_datetime(ot_out) >= get_datetime(bound):
					ot_out = bound
				if get_datetime(start) > ot_in:
					ot_in = start
				if get_datetime(end) < ot_out:
					ot_out = end
			else:
				ot_out = ot_in
	else:
		ot_out = ot_in


	return (ot_in, ot_out)

def get_ndiff(entry):

	if entry.get('nd_start') and entry.get('nd_end') and not frappe.db.get_value("Employee", entry['employee'], "ignore_nd"):
		#get ND start and end
		nd_start, nd_end  = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_start')) ), get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_end')) )
		if entry.get('nd_start') > entry.get('nd_end'):
			nd_end = get_datetime( str( add_days(entry.get('target_date'), 1) ) +" "+ str(entry.get('nd_end')) )

		#set min ND and max ND
		min_nd, max_nd, nd_pro  = entry.get('nd_start'),  entry.get('nd_end'), 1

		card_in = entry.get('card_in')
		card_out = entry.get('card_out')

		#OB Triggers for nightdiff
		if entry.get('ob_stat') == 1:
			#if wholeday OB and no in and out logs set in and out as OB
			if (not entry.get('card_in')) and (not entry.get('card_out')):
				card_in = entry.get('ob_in')
				card_out = entry.get('ob_out')

			elif entry.get('card_in') and entry.get('card_out'):
				card_in = entry.get('card_in')
				if entry.get('ob_in') < entry.get('card_in'):
					card_in = entry.get('ob_in')

				card_out = entry.get('card_out')
				if entry.get('ob_out') > entry.get('card_out'):
					card_out = entry.get('ob_out')

		elif entry.get('ob_stat') == 3:
			if entry.get('card_in') and entry.get('card_out'):
				card_out = entry.get('card_out')
				if entry.get('ob_out') > entry.get('card_out'):
					card_out = entry.get('ob_out')

		#check shift if eligible for nightdiff based from time in and time out:
		min_nd, max_nd, nd_pro = get_ndiff_min_max(nd_start, nd_end, entry.get('time_out'), entry.get('time_in'))
		if card_in and card_out and nd_pro == 1:
			nd_in, nd_out, get_nd = get_ndiff_min_max(min_nd, max_nd, card_out, card_in)
			if get_nd:
				entry['nightdiff'] = abs((nd_out - nd_in).total_seconds())

		#early nightdiff No need for early nightdiff ND should be insided shift
		if card_in and card_out:
			nd_early_start = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_end')) )
			if entry.get('time_in') <= nd_early_start:
				if get_datetime(entry.get('card_in')) < nd_early_start:
					if get_datetime(entry.get('card_in')) < get_datetime(entry.get('time_in')):
						entry['nightdiff'] = (abs(( get_datetime(entry.get('time_in')) - nd_early_start ).total_seconds())) + entry['nightdiff']
					else:
						entry['nightdiff'] = (abs(( get_datetime(entry.get('card_in')) - nd_early_start ).total_seconds())) + entry['nightdiff']

	return entry

def get_ndiff_min_max(_start, _end, _out, _in):

	fmin = _start
	fmax = _start
	fpro = 1

	if _out > _start:
		fmax = _out
		if _out >= _end:
			fmax = _end
	else:
		fpro = 0 

	if _start >= _in:
		fmin = _start
	elif _in > _start:
		fmin = _in
		if _in >= _end:
			fpro = 0

	return fmin, fmax, fpro

def get_late(entry):
	if entry.get('lv_status') == 2 and entry['card_in']: #get late if leave is 1sthalf halfday
		if entry.get('card_in') > entry.get('break_end') + datetime.timedelta(minutes=entry.get('b_grace')):
			entry['late'] += abs((entry.get('card_in') - entry.get('break_end')).total_seconds())
			entry['late_list'].append({'from_time': entry.get('break_end'), 'to_time': entry.get('card_in')})

	elif entry.get('lv_status') == 3 and entry['card_in']: #get late if leave is 2ndhalf halfdays
		if entry.get('card_in') > entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')):
			entry['late'] += (entry.get('card_in') - entry.get('time_in')).total_seconds()
			entry['late_list'].append({'from_time': entry.get('time_in'), 'to_time': entry.get('card_in')})

	else: #get normal late if no leave
		if entry.get('card_in') and entry.get('lv_status') != 1:
			if entry.get('ob_stat') >= 1 and entry.get('ob_in') < entry.get('card_in'): #if has OB and is lesser than card in
				if entry.get('ob_in') > entry.get('break_end') + datetime.timedelta(minutes=entry.get('grace')) : #if OB is in second half
					entry['late'] += abs((entry.get('ob_in') - entry.get('break_end')).total_seconds())
					entry['late_list'].append({'from_time': entry.get('break_end'), 'to_time': entry.get('ob_in')})

					entry['late'] += abs((entry.get('break_start') - entry.get('time_in')).total_seconds())
					entry['late_list'].append({'from_time': entry.get('time_in'), 'to_time': entry.get('break_start')})

				else: #if OB is in first half
					if entry.get('ob_in') > entry.get('break_start'):
						entry['late'] += abs((entry.get('break_start') - entry.get('time_in')).total_seconds())
						entry['late_list'].append({'from_time': entry.get('time_in'), 'to_time': entry.get('break_start')})

					else:
						if entry.get('ob_in') > entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')) :
							entry['late'] += abs((entry.get('ob_in') - entry.get('time_in')).total_seconds())
							entry['late_list'].append({'from_time': entry.get('time_in'), 'to_time': entry.get('ob_in')})

			else:
				if entry.get('card_in') > entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')):

					if entry['graceperiod_late']:
						entry['late'] += ( entry.get('card_in') - ( entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace'))) ).total_seconds()
						entry['late_list'].append({'from_time': ( entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace'))), 'to_time': entry.get('card_in')})

						if entry.get('card_in') > entry.get('break_start'): #Reduce late based from Break Time
							if entry.get('card_in') > entry.get('break_end'): #Reduce late Beyond Break Time
								entry['late'] -= abs((entry.get('break_start') - entry.get('break_end')).total_seconds())
							else:
								entry['late'] -= abs((entry.get('card_in') - entry.get('break_start')).total_seconds())
					else:
						entry['late'] += (entry.get('card_in') - entry.get('time_in')).total_seconds()
						entry['late_list'].append({'from_time': entry.get('time_in'), 'to_time': entry.get('card_in')})

						if entry.get('card_in') > entry.get('break_start'): #Reduce late based from Break Time
							if entry.get('card_in') > entry.get('break_end'): #Reduce late Beyond Break Time
								entry['late'] -= abs((entry.get('break_start') - entry.get('break_end')).total_seconds())
							else:
								entry['late'] -= abs((entry.get('card_in') - entry.get('break_start')).total_seconds())


				if entry.get('ob_stat') == 1 and get_datetime(entry.get('card_out')) <= get_datetime(entry.get('time_in')):

					if entry.get('ob_in') > entry.get('time_in') and entry.get('ob_in') <= entry.get('break_start'):
						entry['late'] += (entry.get('ob_in') - entry.get('time_in')).total_seconds()
						entry['late_list'].append({'from_time': entry.get('time_in'), 'to_time': entry.get('ob_in')})

					if entry.get('ob_in') >= entry.get('break_end') and entry.get('ob_in') < entry.get('time_out'):
						entry['late'] += (entry.get('ob_in') - entry.get('break_end')).total_seconds()
						entry['late_list'].append({'from_time': entry.get('break_end'), 'to_time': entry.get('ob_in')})

						entry['late'] += (entry.get('break_start') - entry.get('time_in')).total_seconds()
						entry['late_list'].append({'from_time': entry.get('time_in'), 'to_time': entry.get('break_start')})

					if entry.get('ob_in') > entry.get('break_start') and entry.get('ob_in') < entry.get('break_end'):
						entry['late'] += (entry.get('break_start') - entry.get('time_in')).total_seconds()
						entry['late_list'].append({'from_time': entry.get('time_in'), 'to_time': entry.get('break_start')})
		
		else: #if no card in check for OB
			if entry.get('ob_stat') > 1:
				#if OB is in 2nd Half
				if entry.get('ob_stat') == 3: 
					if entry.get('ob_in') > entry.get('break_end') + datetime.timedelta(minutes=entry.get('grace')) and not entry.get('lv_status') == 3:
						if not (entry.get('ob_in') >= entry.get('time_out') and entry.get('lv_status') == 3):
							entry['late'] += abs((entry.get('ob_in') - entry.get('break_end')).total_seconds())
							entry['late_list'].append({'from_time': entry.get('break_end'), 'to_time': entry.get('ob_in')})

					if entry.get('ob_in') >= entry.get('break_start') and not entry.get('lv_status') == 2:
						if not (entry.get('ob_in') >= entry.get('time_out') and entry.get('lv_status') == 3):
							entry['late'] += abs((entry.get('time_in') - entry.get('break_start')).total_seconds())
							entry['late_list'].append({'from_time': entry.get('time_in'), 'to_time': entry.get('break_start')})

				#if OB is in 1st Half
				elif entry.get('ob_stat') == 2:
					if entry['graceperiod_late']:
						if entry.get('ob_in') > entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')):
							entry['late'] += abs((entry.get('ob_in') - (entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')))).total_seconds())
							entry['late_list'].append({'from_time': entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')), 'to_time': entry.get('ob_in')})
					else:
						if entry.get('ob_in') > entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')):
							entry['late'] += abs((entry.get('ob_in') - entry.get('time_in')).total_seconds())
							entry['late_list'].append({'from_time': entry.get('time_in'), 'to_time': entry.get('ob_in')})

					if entry.get('ob_in') > entry.get('break_end') + datetime.timedelta(minutes=entry.get('grace')):
						entry['late'] += abs((entry.get('ob_in') - entry.get('break_end')).total_seconds())
						entry['late_list'].append({'from_time': entry.get('break_end'), 'to_time': entry.get('ob_in')})
			else:
				#get late on time in if full time OB
				if entry.get('ob_stat') == 1:
					#if there is no leave on first half
					if entry.get('lv_status') != 2:
						if entry['graceperiod_late']:
							if entry.get('ob_in') > entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')):
								entry['late'] += abs((entry.get('ob_in') - (entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')))).total_seconds())
								entry['late_list'].append({'from_time': entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')), 'to_time': entry.get('ob_in')})
						else:
							if entry.get('ob_in') > entry.get('time_in') + datetime.timedelta(minutes=entry.get('grace')):
								entry['late'] += abs((entry.get('ob_in') - entry.get('time_in')).total_seconds())
								entry['late_list'].append({'from_time': entry.get('time_in'), 'to_time': entry.get('ob_in')})

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

	if entry.get('lv_status') == 2 and entry['card_out']: #get undertime if leave is 1sthalf halfday
		if entry.get('ob_stat') == 1:
			if entry.get('card_out') > entry.get('ob_out'):
				if entry.get('card_out') < entry.get('time_out'):
					entry['undertime'] += abs((entry.get('card_out') - entry.get('time_out')).total_seconds())
					entry['ut_list'].append({'from_time': entry.get('card_out'), 'to_time': entry.get('time_out')})
			else:
				if entry.get('ob_out') < entry.get('time_out'):
					entry['undertime'] += abs((entry.get('ob_out') - entry.get('time_out')).total_seconds())
					entry['ut_list'].append({'from_time': entry.get('ob_out'), 'to_time': entry.get('time_out')})
		else:
			if entry.get('card_out') < entry.get('time_out'):
				entry['undertime'] += abs((entry.get('card_out') - entry.get('time_out')).total_seconds())
				entry['ut_list'].append({'from_time': entry.get('card_out'), 'to_time': entry.get('time_out')})

	elif entry.get('lv_status') == 3 and entry['card_out']: #get undertime if leave is 2ndhalf halfday
		if entry.get('ob_stat') == 1:
			if entry.get('ob_out') < entry.get('break_start'):
				entry['undertime'] += abs((entry.get('ob_out') - entry.get('break_start')).total_seconds())
				entry['ut_list'].append({'from_time': entry.get('ob_out'), 'to_time': entry.get('break_start')})

		else:
			if entry.get('card_out') < entry.get('break_start'):
				entry['undertime'] += abs((entry.get('card_out') - entry.get('break_start')).total_seconds())
				entry['ut_list'].append({'from_time': entry.get('card_out'), 'to_time': entry.get('break_start')})

	else:	
		if entry.get('card_out') and entry.get('lv_status') != 1:
			if entry.get('ob_stat') >= 1:
				if get_datetime(entry.get('card_out')) > get_datetime(entry.get('ob_out')) and not (get_datetime(entry.get('card_in')) >= get_datetime(entry.get('time_out')) or get_datetime(entry.get('card_out')) <= get_datetime(entry.get('time_in'))):
					if entry.get('card_out') < entry.get('time_out'):
						if entry.get('card_out') >= entry.get('break_end'):
							entry['undertime'] += abs((entry.get('card_out') - entry.get('time_out')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('card_out'), 'to_time': entry.get('time_out')})

						if entry.get('card_out') > entry.get('break_start') and entry.get('card_out') < entry.get('break_end'):
							entry['undertime'] += abs((entry.get('break_end') - entry.get('time_out')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('break_end'), 'to_time': entry.get('time_out')})

						if entry.get('card_out') <= entry.get('break_start'):
							entry['undertime'] += abs((entry.get('card_out') - entry.get('break_start')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('card_out'), 'to_time': entry.get('break_start')})

							entry['undertime'] += abs((entry.get('break_end') - entry.get('time_out')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('break_end'), 'to_time': entry.get('time_out')})

				else:
					if entry.get('ob_out') < entry.get('time_out'):
						if entry.get('ob_out') >= entry.get('break_end'):
							entry['undertime'] += abs((entry.get('ob_out') - entry.get('time_out')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('ob_out'), 'to_time': entry.get('time_out')})

						if entry.get('ob_out') > entry.get('break_start') and entry.get('ob_out') < entry.get('break_end'):
							entry['undertime'] += abs((entry.get('break_end') - entry.get('time_out')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('break_end'), 'to_time': entry.get('time_out')})

						if entry.get('ob_out') <= entry.get('break_start'):
							entry['undertime'] += abs((entry.get('ob_out') - entry.get('break_start')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('ob_out'), 'to_time': entry.get('break_start')})

							entry['undertime'] += abs((entry.get('break_end') - entry.get('time_out')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('break_end'), 'to_time': entry.get('time_out')})

			else:
				if entry.get('card_out') < entry.get('time_out'):
					if entry['suspension'] != 3:
						if entry.get('card_out') < entry.get('break_end'):
							entry['undertime'] -= abs((entry.get('card_out') - entry.get('break_end')).total_seconds())
							entry['undertime'] += abs((entry.get('card_out') - entry.get('time_out')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('card_out'), 'to_time': entry.get('time_out')})

						else:
							entry['undertime'] += abs((entry.get('card_out') - entry.get('time_out')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('card_out'), 'to_time': entry.get('time_out')})

						if entry.get('card_out') < entry.get('break_start'):
							entry['undertime'] += abs((entry.get('card_out') - entry.get('break_start')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('card_out'), 'to_time': entry.get('break_start')})

		else: #if no card in check for OB
			
			if entry.get('ob_stat') > 1:
				if entry.get('ob_out') <= entry.get('break_end'): #if OB is in first half
					if not entry.get('lv_status') == 3:
						entry['undertime'] += abs((entry.get('break_end') - entry.get('time_out')).total_seconds())
						entry['ut_list'].append({'from_time': entry.get('break_end'), 'to_time': entry.get('time_out')})

						if entry.get('ob_out') < entry.get('break_start'): #Add undertime Beyond Break Time
							entry['undertime'] += abs((entry.get('ob_out') - entry.get('break_start')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('ob_out'), 'to_time': entry.get('break_start')})
				if entry.get('ob_out') > entry.get('break_end') and entry.get('lv_status') == 3:
					pass
				if entry.get('ob_out') > entry.get('break_end') and not entry.get('lv_status') == 3:
					if entry.get('ob_out') < entry.get('time_out'): #if OB is wholeday
						entry['undertime'] += abs((entry.get('ob_out') - entry.get('time_out')).total_seconds())
						entry['ut_list'].append({'from_time': entry.get('ob_out'), 'to_time': entry.get('time_out')})
			else:
				if entry.get('ob_stat') == 1:
					if entry.get('ob_out') < entry.get('time_out'): #if OB is wholeday
						if not (entry.get('lv_status') == 1 or entry.get('lv_status') == 3):
							entry['undertime'] += abs((entry.get('ob_out') - entry.get('time_out')).total_seconds())
							entry['ut_list'].append({'from_time': entry.get('ob_out'), 'to_time': entry.get('time_out')})

	#if entry.get('lv_status') == 3 or entry.get('ob_stat') == 3:
	#	entry['undertime'] = 0

	#entry['undertime'], entry['ut_list'] = cto_reduction(entry['undertime'], entry['ut_list'])

	if entry['ut_from'] and entry['ut_to']:
		additional_undertime = 0
		if entry['card_in'] and entry['card_out'] or entry['ob_status']:
			for ut in entry['ut_list']: 
				if not (get_datetime(ut['from_time']) >= get_datetime(entry['ut_to']) or get_datetime(ut['to_time']) <= get_datetime(entry['ut_from'])):
					if get_datetime(ut['from_time']) > get_datetime(entry['ut_from']):
						additional_undertime += abs((entry['ut_from'] - ut['from_time']).total_seconds())
						ut['from_time'] = entry['ut_from']

					if get_datetime(ut['to_time']) < get_datetime(entry['ut_to']):
						additional_undertime += abs((ut['from_time'] - entry['ut_to']).total_seconds())
						ut['to_time'] = entry['ut_to']

		if additional_undertime == 0:
			additional_undertime =+  abs((entry['ut_from'] - entry['ut_to']).total_seconds())

		entry['undertime'] += additional_undertime

	if entry.get('ut_interval'):
		entry['undertime'] = (entry.get('ut_interval') * 60) * int( entry.get('undertime') / (entry.get('ut_interval') * 60))

	return entry

def get_cto(entry, cto):
	start, end = None, None
	counter = 0
	if cto:
		for d in cto:
			cto_log_list = []
			cto_fromtime = None
			cto_totime = None
			if d['use_target_date'] == entry['target_date']:
				entry['cto_links'].append(d.name)
				cto_fromtime = get_datetime( str(d.use_from_date) +" "+ str(d.use_fromtime))
				cto_totime = get_datetime( str(d.use_to_date) +" "+ str(d.use_totime))
				if not (cto_fromtime >= entry.get('break_end') or cto_totime <= entry.get('break_start')):
					if cto_fromtime < entry.get('break_start') and cto_totime > entry.get('break_end'):
						cto_log_list.append({'start': cto_fromtime, 'end': entry.get('break_start')})
						cto_log_list.append({'start': entry.get('break_end'), 'end': cto_totime})
					else:
						if cto_fromtime < entry.get('break_start'):
							cto_log_list.append({'start': cto_fromtime, 'end': entry.get('break_start')})
						if cto_totime > entry.get('break_end'):
							cto_log_list.append({'start': entry.get('break_end'), 'end': cto_totime})

				else:
					cto_log_list.append({'start': cto_fromtime, 'end': cto_totime})

				if cto_log_list:
					for ct in cto_log_list:
						if entry["late"]:
							for l in entry["late_list"]:
								start, end = None, None
								if not (ct['start'] > l['to_time'] or ct['end'] < l['from_time']):
									if ct['start'] > l['from_time']:
										start = ct['start']
									else:
										start = l['from_time']
									if ct['end'] < l['to_time']:
										end = ct['end']
									else:
										end = l['to_time']
									entry['cto'] += abs((start - end).total_seconds())
						if entry["undertime"]:
							for ut in entry["ut_list"]:
								start, end = None, None
								if not (ct['start'] > ut['to_time'] or ct['end'] < ut['from_time']):
									if ct['start'] > ut['from_time']:
										start = ct['start']
									else:
										start = ut['from_time']
									if ct['end'] < ut['to_time']:
										end = ct['end']
									else:
										end = ut['to_time']
									entry['cto'] += abs((start - end).total_seconds())

						if entry["is_absent"]:
							entry['cto'] = d.use_total_hours * 60 * 60
							if cto_fromtime < entry.get('time_in') < cto_totime: 
								entry['cto'] -= abs((cto_fromtime - entry.get('time_in')).total_seconds())
							if cto_fromtime < entry.get('time_out') < cto_totime: 
								entry['cto'] -= abs((entry.get('time_out') - cto_totime).total_seconds())
							if entry["lv_status"] == 1:
								entry['cto'] = 0
							if entry["lv_status"] == 2:
								if not (ct['start'] > entry.get('time_out') or ct['end'] < entry.get('break_end')):
									if ct['start'] > entry.get('break_end'):
										start = ct['start']
									else:
										start = entry.get('break_end')
									if ct['end'] < entry.get('time_out'):
										end = ct['end']
									else:
										end = entry.get('time_out')
									entry['cto'] = abs((start - end).total_seconds())
									break
								else:
									entry['cto'] -=  abs((entry.get('time_in') - entry.get('break_start')).total_seconds())
		
							if entry["lv_status"] == 3:
								if not (ct['start'] > entry.get('break_start') or ct['end'] < entry.get('time_in')):
									if ct['start'] > entry.get('time_in'):
										start = ct['start']
									else:
										start = entry.get('time_in')
									if ct['end'] < entry.get('break_start'):
										end = ct['end']
									else:
										end = entry.get('break_start')
									entry['cto'] = abs((start - end).total_seconds())
									break
								else:
									entry['cto'] -=  abs((entry.get('break_end') - entry.get('time_out')).total_seconds())
							break

	return entry

def get_absent(entry):
	if not entry.get('is_restday') and not entry['is_holiday'] and not entry.get('ob_stat'):
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
					entry["is_absent"] = 1
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

	if entry.get('is_restday') and not entry.get('lv_status') and not entry.get('ob_stat'):
		entry["work"] = 0
		entry["late"] = 0
		entry["undertime"] = 0
		entry["is_absent"] = 0

	if (entry.get('lv_status') > 1 or entry.get('suspension') > 1) and not entry.get('card_out'):
		entry["work"] = 0
		if entry.get('lv_status') == 2 and entry.get('ob_stat') == 3 and not entry.get('is_lwop'):
			entry["is_absent"] = 0
			entry["is_halfday"] = 0

		elif entry.get('lv_status') == 2 and entry.get('ob_stat') == 1 and not entry.get('is_lwop'):
			entry["is_absent"] = 0
			entry["is_halfday"] = 0
		elif entry.get('lv_status') == 3 and entry.get('ob_stat') == 2 and not entry.get('is_lwop'):
			entry["is_absent"] = 0
			entry["is_halfday"] = 0
		elif (entry.get('lv_status') == 2 or entry.get('lv_status') == 3) and (entry.get('ob_stat') == 2 or entry.get('ob_stat') == 3) and entry.get('is_lwop'):
			entry["is_absent"] = 0
			entry["is_halfday"] = 1
		else:
			entry["is_absent"] = 1
			entry["is_halfday"] = 1

	if not entry.get('card_out') and not entry.get('is_restday') and not entry.get('is_holiday') and not entry.get('lv_status') and not entry.get('ob_stat'):
		entry["work"] = 0
		entry["late"] = 0
		entry["undertime"] = 0
		entry["is_absent"] = 1

	if entry.get('lv_status') == 1 or entry.get('suspension') == 1:
		entry["work"] = 0
		entry["late"] = 0
		entry["undertime"] = 0
		entry["is_absent"] = 0

	if not entry.get('card_out') and not entry.get('ob_stat') and not entry.get('early_ob'):
		entry['overtime'] = 0
		entry['overtime_nd'] = 0
		entry['overtime_ex'] = 0
		entry['ot_list'] = ""

	if not entry.get('card_in') and not entry.get('ob_stat') and not entry.get('early_ob'):
		entry['overtime'] = 0
		entry['overtime_nd'] = 0
		entry['overtime_ex'] = 0
		entry['ot_list'] = ""

	return entry

def get_flexible(entry, obs):
	if entry.get('is_flexible'):
		flex_ob_time = 0
		less_break = 0
		diff_break = 0
		lv = 0

		if entry.get('ob_in') and entry.get('ob_out'):
			flex_ob_time = abs((entry.get('ob_in') - entry.get('ob_out')).total_seconds())

			#Flex OB time Less Break Hours from schedule
			if entry.get('break_start') and entry.get('break_end'):
				if entry.get('ob_out') > entry.get('break_start'):
					less_break = abs((entry.get('break_start') - entry.get('ob_out')).total_seconds())
					if entry.get('ob_out') > entry.get('break_end'):
						less_break = abs((entry.get('break_start') - entry.get('break_end')).total_seconds())

					if entry.get('ob_in') >= entry.get('break_end'):
						less_break = 0

				flex_ob_time -= less_break
		if entry.get('card_in') and entry.get('card_out'):
			#Reset Flexible values
			entry['late'], entry['undertime'], entry['work']= 0, 0 ,entry.get('worker_secs')
			if entry.get('flexible_type') == "In-Out":		
				diff = (entry.get('card_out') - entry.get('card_in')).total_seconds() + flex_ob_time
				if entry['lv_status'] == 2 or entry['lv_status'] == 3:
					lv = (entry.get('worker_secs') / 2)
				else:
					diff -= (entry.get('break_mins') * 60)


				if diff < (entry.get('worker_secs')):
					ut = 0
					
					if entry.get('ut_interval'):
						ut = (entry.get('worker_secs') - diff) 
						ut = (entry.get('ut_interval') * 60) * int( ut / (entry.get('ut_interval') * 60))
					else:
						ut = (entry.get('worker_secs') - diff) 
					
					if entry['lv_status'] == 2 or entry['lv_status'] == 3:
						#less half of work time if halfday leave
						ut -= (entry.get('worker_secs') / 2) #used to less UT hours
						 #used to less work hours

					#UT Should not be negative
					if ut < 0:
						ut = 0

					entry['late'] = 0
					entry['undertime'] = ut
					entry['work'] = entry.get('worker_secs') - (ut + lv)
			else:
				#gete late base from flexible start time
				flex_start = entry.get('card_in')
				flex_end = entry.get('card_out')

				if entry.get('ob_stat') == 1:
					if entry.get('ob_in') < entry.get('card_in'):
						flex_start = entry.get('ob_in')

					if entry.get('ob_out') > entry.get('card_out'):
						flex_end = entry.get('ob_out')
				flex = get_datetime( str(entry.get('target_date'))+" "+ str(entry.get('flex_to')) )
				if flex:
					if flex_start > ( flex + datetime.timedelta(minutes=entry.get('grace'))):
						if entry['graceperiod_late']:
							entry['late'] = ( flex_start - (flex + datetime.timedelta(minutes=entry.get('grace'))) ).total_seconds()
							flex_start = get_datetime( str(entry.get('target_date'))+" "+ str(entry.get('flex_to')) )
						else:
							entry['late'] = ( flex_start - flex ).total_seconds()
							flex_start = get_datetime( str(entry.get('target_date'))+" "+ str(entry.get('flex_to')) )

				if get_datetime(flex_end) >= get_datetime(entry.get('break_end')):
					diff_break = entry.get('break_mins') * 60
				#always reduce break mins
				diff = abs( (flex_start - flex_end).total_seconds())  - (diff_break) + flex_ob_time

				#if getdate("2020-01-13") == getdate(entry['target_date']):
				#	frappe.throw(_("{0} {1}").format(flex_start, flex_end))

				#Get Undertime
				if entry.get('lv_status') > 1:
					diff += (entry.get('worker_secs') / 2)
				
				if diff < (entry.get('worker_secs')):
					ut = 0
					if entry.get('ut_interval'):
						ut = (entry.get('worker_secs') - diff) 
						ut = (entry.get('ut_interval') * 60) * int( ut / (entry.get('ut_interval') * 60))
					else:
						ut = (entry.get('worker_secs') - diff) 
					
					entry['undertime'] = ut
					entry['work'] = entry.get('worker_secs') - ut

				if entry.get('lv_status') == 2:
					lv = (entry.get('worker_secs') / 2)
					entry['work'] -= lv
					entry['late'] = 0

				if entry.get('lv_status') == 3:
					lv = (entry.get('worker_secs') / 2)
					entry['work'] -= lv
					entry['undertime'] = 0
		else:
			#if no card in card out get OB hrs
			entry['late'], entry['undertime'], entry['work']= 0, 0 ,entry.get('worker_secs')
			if flex_ob_time > 0:
				if flex_ob_time < entry.get('worker_secs'):
					ut = (entry.get('worker_secs') - flex_ob_time)
					ut = (entry.get('ut_interval') * 60) * int( ut / (entry.get('ut_interval') * 60))
					if (entry.get('lv_status') == 2 and entry.get('ob_stat') == 3) or (entry.get('lv_status') == 3 and entry.get('ob_stat') == 2):
						entry['work'] = entry['work']/2
						ut = 0
					else:
						entry['undertime'] = ut
						entry['work'] = entry.get('worker_secs')  - ut

		#Work should not be greater than assigned work hrs
		if entry['work'] > entry.get('worker_secs'):
			entry['work'] = entry.get('worker_secs')
			entry['undertime'] = 0

def get_final_processing(entry):
	if not entry.get('is_flexible'):
		entry['work'] -= entry['late']
		entry['work'] -= entry['undertime']
		if entry['ext_deduct']:
			for et in entry['ex_tardiness']:
				exc_start, exc_end = None, None
				if et['type'] == "Late":
					for lt in entry['late_list']:
						if not (get_datetime(lt['from_time']) >= get_datetime(et['to_time']) or get_datetime(lt['to_time']) <= get_datetime(et['from_time'])):
	
							if get_datetime(lt['from_time']) > get_datetime(et['from_time']):
								exc_start = get_datetime(lt['from_time'])
							else: 
								exc_start = get_datetime(et['from_time'])
	
							if lt.get('to_time') < et.get('to_time'):
								exc_end = get_datetime(lt['to_time'])
							else: 
								exc_end = get_datetime(et['to_time'])
							
							entry['late'] -= abs((exc_end - exc_start).total_seconds())
							if entry['late'] < 0:
								entry['late'] = 0
	
				if et['type'] == "Undertime":
					for ut in entry['ut_list']:
						if not (get_datetime(ut['from_time']) >= get_datetime(et['to_time']) or get_datetime(ut['to_time']) <= get_datetime(et['from_time'])):
	
							if get_datetime(ut['from_time']) > get_datetime(et['from_time']):
								exc_start = get_datetime(ut['from_time'])
							else: 
								exc_start = get_datetime(et['from_time'])
	
							if ut.get('to_time') < et.get('to_time'):
								exc_end = get_datetime(ut['to_time'])
							else: 
								exc_end = get_datetime(et['to_time'])
	
							entry['undertime'] -= abs((exc_end - exc_start).total_seconds())
							if entry['undertime'] < 0:
								entry['undertime'] = 0
	
		if entry['work'] < 0: 
			entry['work'] = 0

			#entry['late'] = 0
			#entry['undertime'] = 0
			#entry['is_absent'] = 1
	if not entry.get('is_restday') and not entry['is_holiday'] and not entry.get('card_in') and not entry.get('card_out'):
		if entry.get('ob_stat') == 3:
			if entry.get('lv_status') == 2:
				if entry.get('ob_in') >= entry.get('time_out'):
					entry["work"] = 0
					entry["late"] = 0
					entry["undertime"] = 0
					entry["is_absent"] = 1
					entry["is_halfday"] = 1

	if entry.get('lv_status') == 3 and entry.get('ob_stat') == 3:
		if not entry.get('card_in') and not entry.get('card_out'):
			entry["work"] = 0
			entry["is_absent"] = 1

	if not entry.get('is_attendance_base'):
		entry["work"] = 0 if entry.get('is_restday') else (entry.get('work_hours') * 60) * 60
		entry["is_absent"] = 0
		entry["break"] = 0
		entry["late"] = 0
		entry["nightdiff"] = 0
		entry["overtime"] = 0
		entry['overtime_nd'] = 0
		entry['overtime_ex'] = 0
		entry['ot_list'] = ""
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

	#if OB stat covers wholeday and leave status is halfday
	if entry.get('ob_stat')  == 1 and entry.get('lv_status') > 1:
		entry["is_absent"] = 0
		entry["is_halfday"] = 0

	strict_card = flt(frappe.db.get_single_value('Timekeeping Settings', 'strict_nocard'), 8)	
	if entry.get('lv_status') != 1 and not entry.get('card_out') and strict_card:
		entry['is_absent'] = 1
		entry["is_halfday"] = 0
		entry["work"] = 0
		entry["late"] = 0
		entry["undertime"] = 0

	if entry.get('lv_status') != 1 and not entry.get('card_in') and strict_card:
		entry['is_absent'] = 1
		entry["is_halfday"] = 0
		entry["work"] = 0
		entry["late"] = 0
		entry["undertime"] = 0

	#Restday
	if entry.get('is_restday'):
		# Strictly no work, late, undertime absent if restday
		if not entry['is_holiday']:
			entry['work'] = 0
			entry['late'] = 0
			entry['undertime'] = 0
			entry['is_absent'] = 0

	#Holiday
	if entry.get('is_holiday'):
		exemption = 0
		if entry.get('is_sp_holiday'):
			#if Special Holiday treaet as absent
			exemption = 1
		elif (not entry.get('is_sp_holiday')) and entry.get('ab_regho'):
			exemption = 1

		if entry.get('rate_type') == "Daily Rate":
			#daily rate has no card in and card out and holday is not restday and is not OB, set to absent
			if (not entry.get('card_out')) and (not entry.get('card_in')) and (not entry.get('is_restday')) and (not entry.get('ob_stat')) and exemption:
				entry['is_absent'] = 1
			else:
				entry['late'] = 0
				entry['undertime'] = 0
				entry['nightdiff'] = 0 
				entry['is_absent'] = 0				

		else:
			if entry.get('mo_abho'):

				if (not entry.get('card_out')) and (not entry.get('card_in')) and (not entry.get('is_restday')) and exemption:
					entry['is_absent'] = 1
				else:
					entry['late'] = 0
					entry['undertime'] = 0
					entry['nightdiff'] = 0
					entry['is_absent'] = 0
			else:

				# Strictly no work, late, undertime absent for non daily rate if holiday
				if (entry.get('card_in') and entry.get('card_out')) or entry['ob_in']:
					entry['work'] = (entry.get('work_hours') * 60 * 60) #set work hours equal to wholeday of work
				else:
					entry['work'] = 0

				entry['nightdiff'] = 0 
				entry['late'] = 0
				entry['undertime'] = 0
				entry['is_absent'] = 0

	#If not Restday, Holiday, Wholeday Leave and Wholeday OB
	if entry.get('is_attendance_base') and entry.get('is_restday') != 1 and entry.get('is_holiday') != 1 and entry.get('lv_status') != 1 and entry.get('ob_stat') != 1:
		if (not entry.get('card_in')) and (not entry.get('card_out')) and not entry['ob_stat']:
			entry["work"] = 0
			entry["undertime"] = 0
			entry["is_absent"] = 1
			if entry.get('suspension') == 1:
				entry["is_absent"] = 0
				entry["late"] = 0
				entry["work"] = 0
				entry["undertime"] = 0

		if entry.get('card_in') and (not entry.get('card_out')):
			entry["work"] = 0
			entry["undertime"] = 0
			entry["is_absent"] = 1
			if entry.get('suspension') != 3:
				entry["late"] = 0
				
			if entry.get('hd_halfcard') and entry.get('suspension') != 3:
				entry['is_absent'] = 1
				entry["is_halfday"] = 1
				entry["work"] = (entry.get('work_hours') * 60 * 60) / 2
				entry["late"] = 0
				entry["undertime"] = 0
		
		if entry.get('card_out') and (not entry.get('card_in')):
			entry["work"] = 0
			entry["late"] = 0
			entry["is_absent"] = 1
			if entry.get('suspension') != 2:
				entry["undertime"] = 0

			if entry.get('hd_halfcard') and entry.get('suspension') != 2:
				entry['is_absent'] = 1
				entry["is_halfday"] = 1
				entry["work"] = (entry.get('work_hours') * 60 * 60) / 2
				entry["late"] = 0
				entry["undertime"] = 0

	#work suspension if card in and not cardout
	if entry.get('card_in') and not entry.get('card_out'):
		if entry.get('suspension') == 3:
			entry["is_halfday"] = 0
			entry["is_absent"] = 0

	#if whole day work suspension
	if entry.get('suspension') == 1:
		entry["is_absent"] = 0
		entry["is_halfday"] = 0
		entry["late"] = 0
		entry["undertime"] = 0
		entry["work"] = 0

	if entry.get('suspension') == 2 and (entry.get('ob_stat') == 3 or entry.get('ob_stat') == 1):
		entry["is_halfday"] = 0
		entry["is_absent"] = 0
		entry["work"] = (entry.get('work_hours') * 60 * 60) / 2
		entry["late"] = 0

	if entry.get('suspension') == 3 and (entry.get('ob_stat') == 2 or entry.get('ob_stat') == 1):
		entry["is_halfday"] = 0
		entry["is_absent"] = 0
		entry["work"] = (entry.get('work_hours') * 60 * 60) / 2
		entry["undertime"] = 0

	if entry.get('lv_status') == 1:
		entry["is_absent"] = 0
		entry["is_halfday"] = 0
		entry["late"] = 0
		entry["undertime"] = 0
		entry["work"] = 0
		
	if entry.get('lwop_status') and entry.get('pd_lv_status'):
		if (entry.get('lwop_status') == 2 and entry.get('pd_lv_status') == 3) or (entry.get('lwop_status') == 3 and entry.get('pd_lv_status') == 2):
			entry["lv_status"] = 1
			entry["is_absent"] = 0
			entry["is_halfday"] = 1

	if entry.get('lv_status') > 1 and entry.get('work') == 0 and (entry.get('late') or entry.get('undertime')):
		entry["is_absent"] = 1
		entry["late"] = 0
		entry["undertime"] = 0
		if entry.get('pd_lv_status'):
			entry["is_halfday"] = 1

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

	if entry.get('cto') > 0:
		entry["tags"] += " <span class='label label-info'> CTO </span> "

	#ob_tags
	if entry.get('ob_stat') == 1 or entry['ob_links']:
		entry["tags"] += " <span class='label label-success'> Official Business  </span> "
	elif entry.get('ob_stat') == 2:
		entry["tags"] += " <span class='label label-success'> OB 1sthalf </span> "
	elif entry.get('ob_stat') == 3:
		entry["tags"] += " <span class='label label-success'> OB 2ndhalf </span> "

	entry["tags"] += " <span class='label label-success'> Excused Tardiness </span> " if entry.get('ex_tardiness') else ""
	entry["tags"] += " <span class='label label-danger'> Absent </span> " if entry['is_absent'] == 1 and entry['is_attendance_base'] else ""
	entry["tags"] += " <span class='label label-danger'> Late </span> " if entry['late'] > 0 else ""
	entry["tags"] += " <span class='label label-info'>"+ entry['holiday_name'] +"</span>" if entry['is_holiday'] == 1 else ""
	entry["tags"] += " <span class='label label-info'> Special Non-Working </span>" if entry['is_sp_holiday'] == 1 else ""

	entry["tags"] += "<span class='label label-success'>"+cstr(entry['leave_name'])+"</span>" if entry['is_leave'] > 0 else ""
	
	if entry['is_restday']:
		entry["tags"] += "<span class='label label-info'> Rest Day </span> "
	else:
		if not entry['card_in'] and entry['is_attendance_base']:
			entry["tags"] += " <span class='label label-warning'> No Card IN </span> "

		if not entry['card_out'] and entry['is_attendance_base']:
			entry["tags"] += " <span class='label label-warning'> No Card OUT </span> "

	return entry

def get_links(entry):
	for d in entry.get('ot_links'):
		entry["links"] += "<span class='label label-success'><a href='/desk#Form/Overtime Application/"+d+"'> "+d+" </a></span>"

	for d in entry.get('lv_links'):
		entry["links"] += "<span class='label label-info'><a href='/desk#Form/Leave Application/"+d+"'> "+d+" </a></span>"

	for d in entry.get('ob_links'):
		entry["links"] += "<span class='label label-info'><a href='/desk#Form/Official Business Application/"+d+"'> "+d+" </a></span>"

	for d in entry.get('ext_links'):
		entry["links"] += "<span class='label label-success'><a href='/desk#Form/Excuse Tardiness Application/"+d+"'> "+d+" </a></span>"

	for d in entry.get('ut_links'):
		entry["links"] += "<span class='label label-info'><a href='/desk#Form/Undertime Application/"+d+"'> "+d+" </a></span>"

	for d in entry.get('cto_links'):
		entry["links"] += "<span class='label label-success'><a href='/desk#Form/Compensatory Time Off/"+d+"'> "+d+" </a></span>"

	for d in entry.get('dtrp_links'):
		entry["links"] += "<span class='label label-success'><a href='/desk#Form/DTR Problem Application/"+d+"'> "+d+" </a></span>"

	return entry

def get_schedule_daterange(start_date, end_date):
    for n in range( int((end_date - start_date).days) + 1):
        yield start_date + datetime.timedelta(n)

def get_schedule_delta_to_time(delta_obj):
	return (datetime.datetime.min + delta_obj).time()

def get_schedule_get_date(date, start, end, type, is_end):
	if is_end == 1:
		if get_schedule_delta_to_time(start) > get_schedule_delta_to_time(end):
			dt = (datetime.datetime.combine(date, get_schedule_delta_to_time(end) ) + datetime.timedelta(days=1) ).strftime('%Y-%m-%d %H:%M:%S')
		else:
			dt = datetime.datetime.combine(date, get_schedule_delta_to_time(end) ).strftime('%Y-%m-%d %H:%M:%S') 
	else:
		dt = datetime.datetime.combine(date, get_schedule_delta_to_time(start) ).strftime('%Y-%m-%d %H:%M:%S') 

	return dt

def get_schedule(employee, pay_from, pay_to):
	schedule = []
	schedule_entry = {}
	shift_map = {}
	template_map = {}
	shift_list = []
	pay_to = getdate(pay_to)
	pay_from = getdate(pay_from)
	def_sched = frappe.db.get_value("Employee", employee, "default_schedule")
	company = frappe.db.get_value("Employee", employee, "company")

	#set Default
	for def_target_date in get_schedule_daterange(pay_from, pay_to):
		schedule_entry[getdate(def_target_date)] = None

	#Get Work Sched Template
	templates = frappe.db.sql("""SELECT `name`, monday, tuesday, wednesday, thursday, friday, saturday, sunday FROM `tabWork Schedule Template` """,as_dict=True)
	for t in templates:
		template_map[t.name]={
			"0":t.monday,
			"1":t.tuesday,
			"2":t.wednesday,
			"3":t.thursday,
			"4":t.friday,
			"5":t.saturday,
			"6":t.sunday
		}

	#Get Shift Map
	shifts = frappe.db.sql("""SELECT * FROM `tabWork Shift` """, as_dict=True)
	for shft in shifts:
		shift_map[shft.name] = {
			"work_shift": shft['name'],
			"shift_type": shft['work_shift_type'],
			"work_hours": shft['work_hours'],
			"break_mins": shft['break_mins'],
			"time_in": shft['time_in'],
			"time_out": shft['time_out'],
			"break_start": shft['break_start'],
			"break_end": shft['break_end'],
			"nd_start": shft['nd_start'],
			"nd_end": shft['nd_end'],
			"pre_shift": add_to_date( shft['time_in'], hours = (0 - shft['setup_preshift']) ),
			"post_shift": add_to_date( shft['time_out'], hours = shft['end_postshift'] ),
		}
		shift_list.append(shft.name)

	#Get Work Schedule
	employee_work_schedule = frappe.db.sql("""SELECT `name`, employee, company, work_shift, work_hours, break_mins, target_date, shift_type, 
		datetime_in, datetime_out, break_start, break_end, nd_start, nd_end, o_time_in, o_break_in, o_break_out, o_time_out
		FROM `tabWork Schedule` WHERE target_date >= %(from_date)s AND target_date <= %(to_date)s AND employee = %(employee)s
		ORDER BY target_date ASC""",{
		"from_date": pay_from, "to_date": pay_to, "employee": employee,
	}, as_dict=True)
	for ews in employee_work_schedule:
		if schedule_entry[getdate(ews.target_date)] == None:
			schedule_entry[getdate(ews.target_date)] = {
				"employee": employee,
				"company": company,
				"name": ews["name"],
				"target_date": ews["target_date"],
				"work_shift": ews["work_shift"],
				"shift_type": ews["shift_type"],
				"work_hours": ews["work_hours"],
				"break_mins": ews["break_mins"],
				"datetime_in": ews["datetime_in"],
				"datetime_out": ews["datetime_out"],
				"break_start": ews["break_start"],
				"break_end": ews["break_end"],
				"nd_start": ews["nd_start"],
				"nd_end": ews["nd_end"],
				"o_time_in": ews["o_time_in"],
				"o_break_in": ews["o_break_in"],
				"o_break_out": ews["o_break_out"],
				"o_time_out": ews["o_time_out"],
				"is_default_schedule": 0,
			}

	#Get Default Schedule
	if def_sched:
		for td in get_schedule_daterange(pay_from, pay_to):
			if schedule_entry[getdate(td)] == None:
				tmplt = template_map[def_sched][str(td.weekday())]
				schedule_entry[getdate(td)] = {
					"employee": employee,
					"company": company,
					"name": tmplt,
					"target_date": td,
					"work_shift": tmplt,
					"shift_type": shift_map[tmplt]["shift_type"],
					"work_hours": shift_map[tmplt]['work_hours'],
					"break_mins": shift_map[tmplt]['break_mins'],
					"datetime_in": datetime.datetime.strptime( get_schedule_get_date(td, shift_map[tmplt]['time_in'], shift_map[tmplt]['time_out'], shift_map[tmplt]['shift_type'], 0) , '%Y-%m-%d %H:%M:%S'),
					"datetime_out": datetime.datetime.strptime( get_schedule_get_date(td, shift_map[tmplt]['time_in'], shift_map[tmplt]['time_out'], shift_map[tmplt]['shift_type'], 1) , '%Y-%m-%d %H:%M:%S'),
					"break_start": datetime.datetime.strptime( get_schedule_get_date(td, shift_map[tmplt]['break_start'], shift_map[tmplt]['break_end'], shift_map[tmplt]['shift_type'], 0) , '%Y-%m-%d %H:%M:%S'),
					"break_end": datetime.datetime.strptime( get_schedule_get_date(td, shift_map[tmplt]['break_start'], shift_map[tmplt]['break_end'], shift_map[tmplt]['shift_type'], 1) , '%Y-%m-%d %H:%M:%S'),
					"nd_start": datetime.datetime.strptime( get_schedule_get_date(td, shift_map[tmplt]['nd_start'], shift_map[tmplt]['time_out'], shift_map[tmplt]['shift_type'], 0) , '%Y-%m-%d %H:%M:%S'),
					"nd_end": datetime.datetime.strptime( get_schedule_get_date(td, shift_map[tmplt]['nd_start'], shift_map[tmplt]['time_out'], shift_map[tmplt]['shift_type'], 1) , '%Y-%m-%d %H:%M:%S'),
					"o_time_in": "",
					"o_break_in": "",
					"o_break_out": "",
					"o_time_out": "",
					"is_default_schedule": 1,
				}

	#Get Change Schedule Application
	cs_apps = frappe.db.sql(""" SELECT CSA.employee, CSA.approved_on, CSAT.target_date, CSAT.new_shift, CSA.name
		FROM `tabChange Schedule Application` CSA INNER JOIN `tabChange Schedule Application Table` CSAT ON CSAT.parent = CSA.`name` 
		WHERE CSA.employee = %s AND CSA.docstatus = 1 AND CSA.workflow_state = 'Approved' AND CSAT.target_date >= %s AND CSAT.target_date <= %s """,(employee, pay_from, pay_to), as_dict=1)
	for csa in cs_apps:
		schedule_entry[getdate(csa.target_date)] = {
			"employee": employee,
			"company": company,
			"name": csa["name"],
			"target_date": getdate(csa["target_date"]),
			"work_shift": csa["new_shift"],
			"shift_type": shift_map[csa['new_shift']]["shift_type"],
			"work_hours": shift_map[csa['new_shift']]['work_hours'],
			"break_mins": shift_map[csa['new_shift']]['break_mins'],
			"datetime_in": datetime.datetime.strptime( get_schedule_get_date(csa['target_date'], shift_map[csa['new_shift']]['time_in'], shift_map[csa['new_shift']]['time_out'], shift_map[csa['new_shift']]['shift_type'], 0) , '%Y-%m-%d %H:%M:%S'),
			"datetime_out": datetime.datetime.strptime( get_schedule_get_date(csa['target_date'], shift_map[csa['new_shift']]['time_in'], shift_map[csa['new_shift']]['time_out'], shift_map[csa['new_shift']]['shift_type'], 1) , '%Y-%m-%d %H:%M:%S'),
			"break_start": datetime.datetime.strptime( get_schedule_get_date(csa['target_date'], shift_map[csa['new_shift']]['break_start'], shift_map[csa['new_shift']]['break_end'], shift_map[csa['new_shift']]['shift_type'], 0) , '%Y-%m-%d %H:%M:%S'),
			"break_end": datetime.datetime.strptime( get_schedule_get_date(csa['target_date'], shift_map[csa['new_shift']]['break_start'], shift_map[csa['new_shift']]['break_end'], shift_map[csa['new_shift']]['shift_type'], 1) , '%Y-%m-%d %H:%M:%S'),
			"nd_start": datetime.datetime.strptime( get_schedule_get_date(csa['target_date'], shift_map[csa['new_shift']]['nd_start'], shift_map[csa['new_shift']]['time_out'], shift_map[csa['new_shift']]['shift_type'], 0) , '%Y-%m-%d %H:%M:%S'),
			"nd_end": datetime.datetime.strptime( get_schedule_get_date(csa['target_date'], shift_map[csa['new_shift']]['nd_start'], shift_map[csa['new_shift']]['time_out'], shift_map[csa['new_shift']]['shift_type'], 1) , '%Y-%m-%d %H:%M:%S'),
			"o_time_in": "",
			"o_break_in": "",
			"o_break_out": "",
			"o_time_out": "",
			"is_default_schedule": 1,
		}

	for sched in sorted(schedule_entry):
		if schedule_entry[sched]:
			row = {
				"employee": schedule_entry[sched]['employee'],
				"company": schedule_entry[sched]['company'],
				"name": schedule_entry[sched]['name'],
				"target_date": schedule_entry[sched]['target_date'],
				"work_shift": schedule_entry[sched]['work_shift'],
				"shift_type": schedule_entry[sched]['shift_type'],
				"work_hours": schedule_entry[sched]['work_hours'],
				"break_mins": schedule_entry[sched]['break_mins'],
				"datetime_in": schedule_entry[sched]['datetime_in'],
				"datetime_out": schedule_entry[sched]['datetime_out'],
				"break_start": schedule_entry[sched]['break_start'],
				"break_end": schedule_entry[sched]['break_end'],
				"nd_start": schedule_entry[sched]['nd_start'],
				"nd_end": schedule_entry[sched]['nd_end'],
				"o_time_in": schedule_entry[sched]['o_time_in'],
				"o_break_in": schedule_entry[sched]['o_break_in'],
				"o_break_out": schedule_entry[sched]['o_break_out'],
				"o_time_out": schedule_entry[sched]['o_time_out'],
				"is_default_schedule": schedule_entry[sched]['is_default_schedule'],
			}
			schedule.append(row)

	return schedule

def get_actual_logs(employee, pay_from, pay_to):
	result = []
	schedule = get_schedule(employee, pay_from, pay_to)
	for sched in schedule:
		shifts = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(sched['work_shift']), as_dict=True)
		if shifts:
			post_shift_date = getdate(sched['target_date'])
			if shifts[0].time_in > shifts[0].time_out:
				post_shift_date = add_days(getdate(sched['target_date']), 1)
			entry = { 
				"work_shift": sched['work_shift'],
				"target_date": sched['target_date'],
				"pre_shift": add_to_date(get_datetime(str(getdate(sched['target_date']))+" "+ str(shifts[0].time_in)), hours= (0 - shifts[0].setup_preshift) ),
				"end_preshift": add_to_date(get_datetime(str(getdate(sched['target_date']))+" "+ str(shifts[0].time_in)), hours= shifts[0].end_preshift ),
				"post_shift": add_to_date(get_datetime(str(post_shift_date)+" "+ str(shifts[0].time_out)), hours= (0 - shifts[0].setup_postshift) ),
				"end_postshift": add_to_date(get_datetime(str(post_shift_date)+" "+ str(shifts[0].time_out)), hours=shifts[0].end_postshift ),
				"card_in": "",
				"card_out": "",
				"break_in": "",
				"break_out": "",
			}
			dtrp_list = []
			emp_bioid = frappe.db.get_value("Employee", employee, "biometrics_id")
			timecards = get_timecard_list(emp_bioid, sched['target_date'], sched['target_date'] + datetime.timedelta(days=1))
			if timecards:
				dtrp_list = get_dtrp_list(employee, sched['target_date'], sched['target_date'] + datetime.timedelta(days=1), None, 0)
				cards_in, cards_out = get_card_within(entry['pre_shift'], entry['end_preshift'], entry['post_shift'], entry['end_postshift'], timecards, dtrp_list)
				get_sorted_card(entry, cards_in, cards_out)
				result.append(entry)

	return result

def get_shift_map():
	shift_map = {}
	shifts = frappe.db.sql("""SELECT `name`, work_hours, override_hrs, grace_period, b_grace_period, is_restday,
			is_flexible, setup_preshift, setup_postshift, flex_from, flex_to, time_in, time_out, break_start, break_end, break_mins,
			end_preshift, end_postshift, graceperiod_late, straight_ot, flexible_type, nd_end, nd_start, work_shift_type, allow_ot_in_shift
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
			"nd_end": d.nd_end,
			"work_shift_type": d.work_shift_type,
			"time_in": d.time_in,
			"time_out": d.time_out,
			"break_start":d.break_start,
			"break_end":d.break_end,
			"break_mins":d.break_mins,
			"allow_ot_in_shift": d.allow_ot_in_shift
		}

	return shift_map

def get_holiday_list(company, location, from_date, to_date):
	holidays = frappe.db.sql("""SELECT holiday_name, holiday_date, is_special, location FROM `tabHoliday` 
		WHERE company = %s AND holiday_date >= %s AND holiday_date <= %s
		ORDER BY holiday_date ASC""",(company, from_date, to_date), as_dict=True)

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

	ob_apps = frappe.db.sql("""SELECT OBA.`name`, OBAT.target_date, OBAT.from_time, OBAT.to_time, OBAT.hrs, OBAT.is_holiday, OBAT.is_excluded, OBAT.to_date
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
	by_adjustment = ""

	cto_apps = frappe.db.sql("""SELECT `name`, use_total_hours, use_target_date FROM `tabCompensatory Time Off` 
		WHERE workflow_state = 'Approved' AND employee = %s AND use_target_date >= %s AND use_target_date <= %s
		AND `type` = 'Use' {by_adjustment} """.format( by_adjustment=by_adjustment ), (employee, from_date, to_date), as_dict=1)
	
	return cto_apps

def get_ext_list(employee, from_date, to_date, approval_cutoff, adjustment):
	by_adjustment = "" if adjustment == 1 else "AND approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' "

	ext_apps = frappe.db.sql("""SELECT `name`, `date`, from_time, to_time, `type` FROM `tabExcuse Tardiness Application` 
		WHERE workflow_state = 'Approved' AND employee = %s AND `date` >= %s 
		AND `date` <= %s {by_adjustment} """.format( by_adjustment=by_adjustment ), (employee, from_date, to_date), as_dict=1)
	
	return ext_apps

def get_wss_list(employee, from_date, to_date, approval_cutoff, adjustment):
	by_adjustment = "" if adjustment == 1 else "AND approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' "	

	ws_apps = frappe.db.sql(""" SELECT suspension_date, suspension_start, suspension_end 
		FROM `tabWork Suspension` WS 
		INNER JOIN `tabWork Suspension Apply` WSA ON WSA.parent = WS.`name` WHERE WS.docstatus = 1 AND WSA.employee = %s AND suspension_date >= %s 
		AND suspension_date <= %s  """.format( by_adjustment=by_adjustment ), (employee, from_date, to_date), as_dict=1)

	return ws_apps

def get_csa_list(employee, from_date, to_date, approval_cutoff, adjustment):
	by_adjustment = "" #if adjustment == 1 else "AND CSA.approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' "	

	cs_apps = frappe.db.sql(""" SELECT CSA.employee, CSA.approved_on, CSAT.target_date, CSAT.new_shift
		FROM `tabChange Schedule Application` CSA 
		INNER JOIN `tabChange Schedule Application Table` CSAT ON CSAT.parent = CSA.`name` 
		WHERE CSA.docstatus = 1 AND workflow_state = 'Approved' AND CSA.`employee` = %s
		AND CSAT.target_date >= %s AND CSAT.target_date <= %s """.format( by_adjustment=by_adjustment ), (employee, from_date, to_date), as_dict=1)

	return cs_apps

def get_dtrp_list(employee, from_date, to_date, approval_cutoff, adjustment):
	by_adjustment = "" #if adjustment == 1 else "AND DA.approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' "

	dtrp_apps = frappe.db.sql("""SELECT DA.`name`, DA.`employee`, TIMESTAMP(DA.`target_date`, DT.`request`) as card_datetime, 
		DA.`target_date`, DT.`request`, DT.`type`, DA.`approved_on`, DT.`card_type`
		FROM `tabDTR Problem Table` DT INNER JOIN `tabDTR Problem Application` DA ON DT.`parent`=DA.`name` 
		WHERE DA.`workflow_state` = 'Approved' AND DA.`employee` = %s
		AND DA.`target_date` >= %s AND DA.`target_date` <= %s {by_adjustment}
		ORDER BY card_datetime """.format( by_adjustment=by_adjustment ), (employee, from_date, to_date), as_dict=1)

	return dtrp_apps

def get_card_within(pre_shift, max_preshift, post_shift, max_postshift, timecard_list, dtrp):
	cards_in = []
	cards_out = []
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

	no_card_in, no_card_out, no_break_out, no_break_in = 1, 1, 1, 1
	for dt in dtrp:
		for c_in in cards_in:
			if pre_shift <= dt['card_datetime'] <= max_preshift and dt['card_type'] == c_in['card_type']:
				c_in['card_name'] = dt['name']
				c_in['card_date'] = dt['target_date']
				c_in['card_time'] = dt['request']
				c_in['card_datetime'] = dt['card_datetime']
				c_in['card_type'] = dt['card_type']

				if dt['card_type'] == 0:
					no_card_in = 0
				if dt['card_type'] == 2:
					no_break_out = 0

		for c_out in cards_out:
			if post_shift <= dt['card_datetime'] <= max_postshift and dt['card_type'] == c_out['card_type']:
				c_out['card_name'] = dt['name']
				c_out['card_date'] = dt['target_date']
				c_out['card_time'] = dt['request']
				c_out['card_datetime'] = dt['card_datetime']
				c_out['card_type'] = dt['card_type']

				if dt['card_type'] == 1:
					no_card_out = 0
				if dt['card_type'] == 3:
					no_break_in = 0
		
		if no_card_in == 1 or no_break_out == 1:
			if pre_shift <= dt['card_datetime'] <= max_preshift and (dt['card_type'] == 0 or dt['card_type'] == 2):
				cards_in.append({
					"card_name": dt['name'],
					"card_date": dt['target_date'],
					"card_time": dt['request'],
					"card_datetime": dt['card_datetime'],
					"card_type": dt['card_type']
				})

		if no_card_out == 1 or no_break_in == 1:
			if post_shift <= dt['card_datetime'] <= max_postshift and (dt['card_type'] == 1 or dt['card_type'] == 3):
				cards_out.append({
					"card_name": dt['name'],
					"card_date": dt['target_date'],
					"card_time": dt['request'],
					"card_datetime": dt['card_datetime'],
					"card_type": dt['card_type']
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
	timecard_list = frappe.db.sql("""SELECT TIMESTAMP(date, time) as card_datetime, card_type, `name`, `time` FROM `tabTime Card` 
		WHERE is_disabled = 0 AND biometrics_id = %(bio)s AND date >= %(from_date)s AND date <= %(to_date)s
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
	#for d in entry.get('ot_list'):
	#	ot = frappe.new_doc("Overtime")
	#	ot.update({
	#		"employee": d.get('employee'),
	#		"target_date": d.get('target_date'),
	#		"ot_code": d.get('ot_code'),	
	#		"hrs": d.get('ot_hrs'),
	#		"linked_ot": d.get('linked_ot'),
	#	})
	#	ot.insert()

	entry['ot_list'] = 0.0
	entry['ot_links'] = None
	entry['lv_links'] = None
	entry['ob_links'] = None
	entry['ext_links'] = None
	entry['ut_links'] = None
	entry['cto_links'] = None
	entry['dtrp_links'] = None

def get_defaults(emp, sched, shift_map, overrides):
	post_shift_date = getdate(sched['target_date'])
	if shift_map[sched['work_shift']]['time_in'] > shift_map[sched['work_shift']]['time_out']:
		post_shift_date = add_days(getdate(sched['target_date']), 1)

	entry = {
		#employe settings
		"employee": emp.name,
		"company": emp.company,
		"location": emp.location,
		"department": emp.department,
		"rate_type": emp.rate_type,
		"worker_hrs": emp.no_hours,
		"worker_secs": (emp.no_hours * 60) * 60,
		"is_attendance_base": emp.is_attendance_base,
		#schedule settings
		"target_date": sched['target_date'],
		"work_shift": sched['work_shift'],
		"pre_shift": add_to_date(get_datetime(str(getdate(sched['target_date']))+" "+ str(shift_map[sched['work_shift']]['time_in'])), hours= (0 - shift_map[sched['work_shift']]['setup_preshift']) ),
		"end_preshift": add_to_date(get_datetime(str(getdate(sched['target_date']))+" "+ str(shift_map[sched['work_shift']]['time_in'])), hours= shift_map[sched['work_shift']]['end_preshift'] ),
		"post_shift": add_to_date(get_datetime(str(post_shift_date)+" "+ str(shift_map[sched['work_shift']]['time_out'])), hours= (0 - shift_map[sched['work_shift']]['setup_postshift']) ),
		"end_postshift": add_to_date(get_datetime(str(post_shift_date)+" "+ str(shift_map[sched['work_shift']]['time_out'])), hours=shift_map[sched['work_shift']]['end_postshift'] ),
		"time_in": shift_map[sched['work_shift']]['time_in'],
		"time_out": shift_map[sched['work_shift']]['time_out'],
		"break_start": shift_map[sched['work_shift']]['break_start'],
		"break_end": shift_map[sched['work_shift']]['break_end'],
		"nd_start": shift_map[sched['work_shift']]['nd_start'],
		"nd_end": shift_map[sched['work_shift']]['nd_end'],
		"work_shift_type": shift_map[sched['work_shift']]['work_shift_type'],
		#shift policy
		"work_hours": shift_map[sched['work_shift']]['work_hours'],
		"break_mins": shift_map[sched['work_shift']]['break_mins'],
		"grace": shift_map[sched['work_shift']]['grace_period'],
		"b_grace": shift_map[sched['work_shift']]['b_grace_period'],
		"is_flexible": shift_map[sched['work_shift']]['is_flexible'],
		"flex_from": shift_map[sched['work_shift']]['flex_from'],
		"flex_to": shift_map[sched['work_shift']]['flex_to'],		
		"is_restday": shift_map[sched['work_shift']]['is_restday'],
		"is_default_schedule": sched['is_default_schedule'],
		#general policy
		"is_processed": 0,
		#timecard data
		"card_in": "",
		"card_out": "",
		"override_in": None,
		"override_out": None,			
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
		"overtime_nd": 0.0,
		"overtime_ex": 0.0,
		"ot_in": "",
		"ot_out": "",
		"ot_list": "",
		"is_change_schedule": 0,
		#LEAVE
		"linked_leave": "",
		"leave_name": "",
		"lv_status": 0,

		"is_leave": 0,
		"is_lwop": 0,
		"pd_lv_status": 0,
		"lwop_status": 0,
		#OB
		"linked_ob": "",
		"is_ob": 0,
		"ob_in": "",
		"ob_out": "",
		"ob": 0.0,
		"ob_stat": 0,
		"early_ob": 0,
		"early_ob_in": None,
		"early_ob_out": None,
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
		"ex_tardiness": [],
		"tags": "",
		"links": "",
		#CTO
		"cto": 0.0,
		#SUSPENSION
		"suspension": 0,
		"suspension_start": "",
		"suspension_end": "",
		#LINKs
		"lv_links": [],
		"ot_links": [],
		"ob_links": [],
		"ext_links": [],
		"ut_links": [],
		"cto_links": [],
		"dtrp_links": [],
		#SHIFT POLICIES
		"graceperiod_late": shift_map[sched['work_shift']]['graceperiod_late'],
		"straight_ot": shift_map[sched['work_shift']]['straight_ot'],
		"allow_ot_in_shift": shift_map[sched['work_shift']]['allow_ot_in_shift'],
		"flexible_type": shift_map[sched['work_shift']]['flexible_type'],
		#GLOBAL POLICIES
		"ot_deduct_late": flt(frappe.db.get_single_value('Timekeeping Settings', 'ot_deduct_late'), 8),
		"ot_start_delay": flt(frappe.db.get_single_value('Timekeeping Settings', 'ot_start_delay'), 8),
		"ot_interval": flt(frappe.db.get_single_value('Timekeeping Settings', 'ot_interval'), 8),
		"max_holiday_ot": flt(frappe.db.get_single_value('Timekeeping Settings', 'max_holiday_ot'), 8),
		"late_interval": flt(frappe.db.get_single_value('Timekeeping Settings', 'late_interval'), 8),
		"ut_interval": flt(frappe.db.get_single_value('Timekeeping Settings', 'ut_interval'), 8),
		"ot_strict_logs": flt(frappe.db.get_single_value('Timekeeping Settings', 'ot_strict_logs'), 8),
		"hd_halfcard": flt(frappe.db.get_single_value('Timekeeping Settings', 'hd_halfcard'), 8),
		"ot_dedlt_ho": frappe.db.get_single_value('Timekeeping Settings', 'ot_dedlt_ho'),
		"at_work_rdho": frappe.db.get_single_value('Timekeeping Settings', 'at_work_rdho'),
		"mo_abho": frappe.db.get_single_value('Timekeeping Settings', 'mo_abho'),
		"ab_regho": frappe.db.get_single_value('Timekeeping Settings', 'ab_regho'),
		"ext_deduct": frappe.db.get_single_value('Timekeeping Settings', 'ext_deduct'),
	}
	
	return entry

def init_employee_map(employees, employee, company, pay_from, pay_to, approval_cutoff, adjustment):
	pay_from = getdate(pay_from)
	pay_to = getdate(pay_to)
	emp_map = frappe._dict()
	for emp in employees:
		emp_map.setdefault(emp.name, frappe._dict({
				"employee": emp.name,
				"employee_name": emp.full_name,
				"company": emp.company,
				"employee_details": emp,
				"schedules": [],
				"timecards": [],
				"overrides": [],
				"hls": [],
				"lvs": [],
				"ots": [],
				"obs": [],
				"uts": [],
				"ext": [],
				"cto": [],
				"wss": [],
				"csa": [],
				"dtrp": [],
			})
		)

	get_all_overrides(emp_map, employee, pay_from, pay_to)
	get_all_schedules(emp_map, employee, pay_from, pay_to)
	get_all_timecards(emp_map, employee, pay_from, pay_to + datetime.timedelta(days=1)) #+1 date to get nextday logs
	get_all_holidays(emp_map, pay_from, pay_to)
	#applications
	get_all_leaves(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment)
	get_all_ots(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment)
	get_all_obs(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment)
	get_all_uts(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment)
	get_all_ext(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment)
	get_all_cto(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment)
	get_all_wss(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment)
	get_all_csa(emp_map, employee, pay_from, pay_to + datetime.timedelta(days=1), approval_cutoff, adjustment)
	get_all_dtrp(emp_map, employee, pay_from, pay_to + datetime.timedelta(days=1), approval_cutoff, adjustment)

	return emp_map

def get_all_timecards(emp_map, employee, pay_from, pay_to):
	condition = "AND EMP.name = '"+ cstr(employee) +"'" if employee else ""
	timecards = frappe.db.sql("""SELECT EMP.name as employee, TC.biometrics_id, TIMESTAMP(TC.date, TC.time) as card_datetime, 
		TC.card_type, TC.time FROM `tabTime Card` TC
		INNER JOIN tabEmployee EMP ON EMP.biometrics_id = TC.biometrics_id
		WHERE TC.is_disabled = 0 AND TC.date >= %(from_date)s AND TC.date <= %(to_date)s {condition}
		ORDER BY TC.date, TC.time """.format( condition=condition ),{
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)

	for d in timecards:
		if d.employee in emp_map:
			emp_map[d.employee].timecards.append(d)

def get_all_schedules(emp_map, employee, pay_from, pay_to):		
	condition = "AND employee = '"+ cstr(employee) +"'" if employee else ""
	schedule = frappe.db.sql("""SELECT employee, company, work_shift, target_date, o_time_in, o_break_in, o_break_out, o_time_out
		FROM `tabWork Schedule` 
		WHERE target_date >= %(from_date)s AND target_date <= %(to_date)s {condition}
		ORDER BY target_date ASC""".format( condition=condition ),{
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)

	for d in schedule:
		if d.employee in emp_map:
			emp_map[d.employee].schedules.append({
				"employee": d.employee,
				"company": d.company,
				"work_shift": d.work_shift,
				"target_date": d.target_date,
				"o_time_in": d.o_time_in,
				"o_break_in": d.o_break_in,
				"o_break_out": d.o_break_out,
				"o_time_out": d.o_time_out,
				"is_default_schedule": 0,
				"is_change_schedule": 0,
			})

def get_all_overrides(emp_map, employee, pay_from, pay_to):
	condition = "AND employee = '"+ cstr(employee) +"'" if employee else ""		
	overrides = frappe.db.sql("""SELECT employee, target_date, time_in, break_in, break_out, time_out
		FROM `tabOverride List` 
		WHERE target_date >= %(from_date)s AND target_date <= %(to_date)s {condition}""".format( condition=condition ),{
			"from_date":pay_from,
			"to_date":pay_to,
		},as_dict=True)

	for d in overrides:
		if d.employee in emp_map:
			emp_map[d.employee].overrides.append(d)

def get_all_holidays(emp_map, pay_from, pay_to):
	holidays = frappe.db.sql("""SELECT company, holiday_name, holiday_date, is_special, location FROM `tabHoliday` 
		WHERE holiday_date >= %s AND holiday_date <= %s
		ORDER BY holiday_date ASC""",(pay_from, pay_to), as_dict=True)

	for emp, emp_dict in emp_map.items():
		for ho in holidays:
			if emp_dict['company'] == ho.company:
				emp_dict['hls'].append(ho)

	return holidays

def get_all_leaves(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment):
	conditions_list = []
	if adjustment != 1:
		conditions_list.append("L.approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("L.employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	leaves = frappe.db.sql("""SELECT L.`name`, L.employee, L.leave_type, LA.leave_date, 
		LA.is_half_day, LA.is_second_half, LA.is_holiday, LA.is_excluded, L.is_lwop
		FROM `tabLeave Application Table` LA
		INNER JOIN `tabLeave Application` L ON L.`name` = LA.parent
		WHERE LA.leave_date >= %s AND LA.leave_date <= %s {conditions} AND L.docstatus = '1' AND L.workflow_state = 'Approved'
		ORDER BY LA.leave_date ASC """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	for d in leaves:
		if d.employee in emp_map:
			emp_map[d.employee].lvs.append(d)

def get_all_obs(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment):
	conditions_list = []
	if adjustment != 1:
		conditions_list.append("approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("OBA.employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	ob_apps = frappe.db.sql("""SELECT OBA.`name`, OBA.employee, OBAT.target_date, OBAT.date, OBAT.to_date,OBAT.from_time, OBAT.to_time, OBAT.hrs, OBAT.is_holiday, OBAT.is_excluded 
		FROM `tabOfficial Business Application Table` OBAT
		INNER JOIN `tabOfficial Business Application` OBA  ON OBAT.parent = OBA.`name`
		WHERE OBA.workflow_state = 'Approved' AND OBAT.target_date >= %s 
		AND OBAT.target_date <= %s 
		AND OBAT.is_excluded = 0 {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	for d in ob_apps:
		if d.employee in emp_map:
			emp_map[d.employee].obs.append(d)

def get_all_ots(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment):
	conditions_list = []
	if adjustment != 1:
		conditions_list.append("approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	overtimes = frappe.db.sql("""SELECT `name`, employee, total_hrs, break_hrs, target_date, from_date, to_date, from_time, to_time FROM `tabOvertime Application` 
		WHERE workflow_state = 'Approved' AND target_date >= %s 
		AND target_date <= %s {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	for d in overtimes:
		if d.employee in emp_map:
			emp_map[d.employee].ots.append(d)

def get_all_uts(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment):
	conditions_list = []
	if adjustment != 1:
		conditions_list.append("approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	undertimes = frappe.db.sql("""SELECT `name`, employee, from_time, to_time, from_date, to_date FROM `tabUndertime Application` 
		WHERE workflow_state = 'Approved' AND from_date >= %s 
		AND from_date <= %s {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	for d in undertimes:
		if d.employee in emp_map:
			emp_map[d.employee].uts.append(d)

def get_all_cto(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment):
	conditions_list = []
	if adjustment != 1:
		conditions_list.append("approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")
		
	if employee:
		conditions_list.append("employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	compensatory = frappe.db.sql("""SELECT `name`, employee, use_total_hours, use_target_date, use_from_date, use_to_date, use_fromtime, use_totime FROM `tabCompensatory Time Off` 
		WHERE workflow_state = 'Approved' AND use_target_date >= %s AND use_target_date <= %s
		AND `type` = 'Use' {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)
	
	for d in compensatory:
		if d.employee in emp_map:
			emp_map[d.employee].cto.append(d)

def get_all_ext(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment):
	conditions_list = []
	if adjustment != 1:
		conditions_list.append("approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	ex_tardiness = frappe.db.sql("""SELECT `name`, employee, `date`, from_time, to_time, `type` FROM `tabExcuse Tardiness Application` 
		WHERE workflow_state = 'Approved' AND `date` >= %s 
		AND `date` <= %s {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)
	
	for d in ex_tardiness:
		if d.employee in emp_map:
			emp_map[d.employee].ext.append(d)

def get_all_wss(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment):
	conditions_list = []
	#if adjustment == 1:
	#	conditions_list.append("approved_on >= '"+ cstr(getdate(approval_cutoff)) +"' ")
	#else:
	#	conditions_list.append("approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	ws_apps = frappe.db.sql(""" SELECT employee, suspension_date, suspension_start, suspension_end 
		FROM `tabWork Suspension` WS 
		INNER JOIN `tabWork Suspension Apply` WSA ON WSA.parent = WS.`name` 
		WHERE WS.docstatus = 1 AND suspension_date >= %s 
		AND suspension_date <= %s {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	for d in ws_apps:
		if d.employee in emp_map:
			emp_map[d.employee].wss.append(d)

def get_all_csa(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment):
	conditions_list = []
	multi_csa = {}

	if adjustment != 1:
		conditions_list.append("CSA.approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")#

	if employee:
		conditions_list.append("CSA.employee='"+cstr(employee)+"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	cs_apps = frappe.db.sql(""" SELECT CSA.employee, CSA.approved_on, CSAT.target_date, CSAT.new_shift
		FROM `tabChange Schedule Application` CSA 
		INNER JOIN `tabChange Schedule Application Table` CSAT ON CSAT.parent = CSA.`name` 
		WHERE CSA.docstatus = 1 AND workflow_state = 'Approved' AND CSAT.target_date >= %s AND CSAT.target_date <= %s 
		{conditions} ORDER BY CSA.modified ASC """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	for d in cs_apps:
		if d.employee in emp_map:
			if d.employee not in multi_csa:
				multi_csa[d.employee] = {}

			if d.target_date not in multi_csa[d.employee]:
				multi_csa[d.employee][d.target_date] = []
				
			multi_csa[d.employee][d.target_date].append(d)

	for m in multi_csa:
		for ml in multi_csa[m]:
			xml = max(multi_csa[m][ml], key=lambda x:x['approved_on'])
			emp_map[m].csa.append(xml)

def get_all_dtrp(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment):
	conditions_list = []
	multi_dtrp = {}
	#if adjustment == 1:
	#	conditions_list.append("DA.approved_on >= '"+ cstr(getdate(approval_cutoff)) +"' ")
	#else:
	#	conditions_list.append("DA.approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("DA.employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	dtr_apps = frappe.db.sql(""" SELECT DA.`name`, DA.`employee`, TIMESTAMP(DA.`target_date`, DT.`request`) as card_datetime, 
		DA.`target_date`, DT.`request`, DT.`type`, DA.`approved_on`, DT.`card_type`
		FROM `tabDTR Problem Table` DT INNER JOIN `tabDTR Problem Application` DA ON DT.`parent`=DA.`name` 
		WHERE DA.`workflow_state` = 'Approved'
		AND DA.`target_date` >= %s AND DA.`target_date` <= %s {conditions}
		ORDER BY card_datetime """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	for d in dtr_apps:
		if d.employee in emp_map:
			if d.employee not in multi_dtrp:
				multi_dtrp[d.employee] = {}

			if d.target_date not in multi_dtrp[d.employee]:
				multi_dtrp[d.employee][d.target_date] = {}

			if d.type not in multi_dtrp[d.employee][d.target_date]:
				multi_dtrp[d.employee][d.target_date][d.type] = []

			multi_dtrp[d.employee][d.target_date][d.type].append(d)

	for m in multi_dtrp:
		for ml in multi_dtrp[m]:
			for mlt in multi_dtrp[m][ml]:
				xml = max(multi_dtrp[m][ml][mlt], key=lambda x:x['approved_on'])
				emp_map[m].dtrp.append(xml)

def complete_sched(emp_dict, pay_from, pay_to, template_map):
	pay_from = getdate(pay_from)
	pay_to = getdate(pay_to)
	complete_schedules = []
	for target_date in daterange(pay_from, pay_to):
		has_sched = False
		for idx, sched in enumerate(emp_dict['schedules']):
			if target_date == sched['target_date']:
				complete_schedules.append(sched)
				has_sched = True
				break
		if has_sched ==  False:
			if emp_dict['employee_details']['default_schedule']:
				complete_schedules.append({
					"employee": emp_dict['employee_details']['name'],
					"company": emp_dict['employee_details']['company'],
					"work_shift": template_map[(emp_dict['employee_details']['default_schedule'])][str(target_date.weekday())],
					"target_date": target_date,
					"o_time_in": None,
					"o_break_in": None,
					"o_break_out": None,
					"o_time_out": None,
					"is_default_schedule": 1,
					"is_change_schedule": 0,
				})
	emp_dict['schedules'] = complete_schedules

def change_sched(emp_dict, completed_schedules, csa):
	for d in completed_schedules:
		for cs in csa:
			if cs['target_date'] == d['target_date']:
				d['work_shift'] = cs['new_shift']
				d['is_default_schedule'] = 0
				d['is_change_schedule'] = 1

def processed_def_sched(employee, pay_from, pay_to, completed_schedules):
	att_reg = frappe.db.sql(""" SELECT AR.`employee`, AR.`target_date`, AR.`work_shift`, AR.`is_default_schedule` FROM `tabAttendance Register` AR 
		WHERE AR.`target_date` >= %s AND AR.`target_date` <= %s """,(pay_from, pay_to), as_dict=1)

	for d in completed_schedules:
		for ar in att_reg:
			if (ar.employee == employee) and (ar.is_default_schedule) and (not d['is_change_schedule']):
				if ar['target_date'] == d['target_date']:
					d['work_shift'] = ar['work_shift']

def daterange(start_date, end_date):
    for n in range( int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def get_template_map():
	template_map = {}
	templates = frappe.db.sql("""SELECT `name`, monday, tuesday, wednesday, thursday, friday, saturday, sunday FROM `tabWork Schedule Template`""",as_dict=True)

	for t in templates:
		template_map[t.name]={
			"0":t.monday,
			"1":t.tuesday,
			"2":t.wednesday,
			"3":t.thursday,
			"4":t.friday,
			"5":t.saturday,
			"6":t.sunday
		}
	return template_map
