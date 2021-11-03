from __future__ import unicode_literals
import frappe, datetime, math
from frappe.utils import cint, cstr, flt, nowdate, add_days, getdate, fmt_money, get_datetime, add_to_date, get_time
from frappe import _
from datetime import timedelta, date

def get_attendance(entry, overrides, leaves, holidays, obs, ots, uts, ext, cto, wss, dtrp, tla):
#	if dtrp:
#		for dt in dtrp:
#			if dt['target_date'] == entry['target_date']:
#				entry['is_dtrp'] = 1
#				if dt['name'] not in entry['dtrp_links']:
#					entry['dtrp_links'].append(dt['name'])

	if tla:
		for tl in tla:
			if tl['target_date'] == entry['target_date']:
				entry['is_tla'] = 1
				if tl['name'] not in entry['tla_links']:
					entry['tla_links'].append(tl['name'])

	entry['has_timelog_override'] = 0
	for over in overrides:
		if over['target_date'] == entry['target_date']:
			entry['has_timelog_override'] = 1
			if over.get("time_in"):
				entry['card_in'] = get_datetime(str(over.get("time_in")))

			if over.get("time_out"):
				entry['card_out'] = get_datetime(str(over.get("time_out")))

			if over.get("break_out"):
				entry['break_out'] = get_datetime(str(over.get("break_out")))

			if over.get("break_in"):
				entry['break_in'] = get_datetime(str(over.get("break_in")))

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

	if entry['is_multi_break']:
		#entry['break_start'] = entry['break_start']
		#entry['break_start'] = entry['break_end']
		entry['break_out'] = None
		entry['break_in'] = None

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
			if ut['target_date'] == entry['target_date']:
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
	already_wholeday_suspended = 0
	for ws in wss:
		if getdate(ws.suspension_date) == getdate(entry['target_date']):	
			if ws.suspension_start and ws.suspension_end:
				if not entry['suspension']:
					entry['suspension'] = 1
				if ws.suspension_start  >= entry['break_end']:
					if entry['suspension'] == 2:
						entry['suspension'] = 1
						break
					entry['suspension'] = 3
				else:	
					if ws.suspension_end <= entry['break_end']:
						if entry['suspension'] == 3:
							entry['suspension'] = 1
							break
						entry['suspension'] = 2

	entry['late_list'] = []
	entry['ut_list'] = []
	entry['cto_list'] = []
	entry['late_deduction'] = 0
	entry['ut_deduction'] = 0
	entry['late_without_int'] = 0
	entry['flex_in_out'] = []
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
		start = None
		end = None
		if entry.get('card_in') and entry.get('card_out'):
			entry['work'] = (entry.get('work_hours') * 60) * 60
			if entry['suspension']:
				if entry['suspension'] == 1:
					entry['work'] = 0
				if entry['suspension'] == 2:
					if entry.get('card_in') < entry.get('break_start'):
						if entry.get('card_out') < entry.get('break_start'):
							entry['work'] = abs((entry.get('card_in') - entry.get('card_out')).total_seconds())
						else:
							entry['work'] = abs((entry.get('card_in') - entry.get('break_start')).total_seconds())
					else:
						entry['work'] = 0
				if entry['suspension'] == 3:
					if entry.get('card_out') > entry.get('break_end'):
						if entry.get('card_in') > entry.get('break_end'):
							entry['work'] = abs((entry.get('card_in') - entry.get('card_out')).total_seconds())
						else:
							entry['work'] = abs((entry.get('break_end') - entry.get('card_out')).total_seconds())
					else:
						entry['work'] = 0
		else:
			if entry.get('ob_stat') == 1:
				if entry['suspension'] == 1:
					entry['work'] = 0
				else:
					entry['work'] = (entry.get('work_hours') * 60) * 60
					if entry["is_halfday"] == 1:
						entry['actual_work'] = entry['work']
						if not frappe.get_single_value('Timekeeping Settings', 'hd_actualwork'): 
							entry['work'] = entry['work'] / 2 
			if entry.get('ob_stat') > 1 and not entry['card_in'] and not entry['card_out']:
				if not entry["lv_status"]:
					if entry.get('ob_stat') == entry['suspension']:
						entry['work'] = 0
					else:
						entry['work'] = (entry.get('work_hours') * 60) * 60
						entry['work'] = entry['work'] / 2

	return entry

def get_overtime(entry, ot_apps):
	ot_list = []
	work_shift = []
	ot_map = get_overtime_map()
	total_ot, total_brk, total_ot_n, total_ot_nd, total_ot_ex, total_otndex = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
	otho_total, otho_used = 0.00, 0.00
	nd_start = None
	nd_end = None
	nd_early_start = None
	ot_earlynd = None
	ot_latend = None
	ot_ndex_start = None
	ot_ndex_end = None
	ot_ex_start = None
	ot_ex_end = None
	total_ot_earlynd, total_ot_latend = 0, 0
	strict_logs = frappe.db.get_single_value('Timekeeping Settings', 'ot_strict_logs')
	ded_late_ot = frappe.db.get_single_value('Timekeeping Settings', 'ded_late_ot')
	ded_ut_ot = frappe.db.get_single_value('Timekeeping Settings', 'ded_ut_ot')
	min_ot_mins = frappe.db.get_single_value('Timekeeping Settings', 'min_ot_mins')
	enable_otndex = frappe.db.get_single_value('Timekeeping Settings', 'enable_otndex')
	ded_brk_otreg = frappe.db.get_single_value('Timekeeping Settings', 'ded_brk_otreg')	
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
			ot_int_start = None
			per_time_with_ot = []
			is_break_deducted, is_nd_break_deducted = 0, 0
			ot_hrs, ot_nd, ot_normal, org_ot_normal = 0, 0, 0, 0
			ot_log_list, ots = [], []
			log_used = 0

			if getdate(d.get('target_date')) == entry.get('target_date'):
				counter += 1
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
				ot_filed = abs((ot_in - ot_out).total_seconds()) 
				if entry.get('ot_deduct_late') and not entry.get('is_flexible') and not entry.get('dn_ot_late'):
					if min_ot_mins > 0:
						if flt(ot_filed/60, 8) < flt(min_ot_mins, 8):
							ot_filed = 0
					if entry.get('is_restday') < 1:
						if entry.get('is_holiday'):
							if entry.get('ot_dedlt_ho'):
								ot_in = add_to_date(ot_in, hours=( entry.get('late') / 60 / 60 ))
								if ded_late_ot:
									entry['late_deduction'] = entry['late']
									entry['late'] -= ot_filed
									if entry.get('late') < 0:
										entry['late_deduction'] = ot_filed


						else:
							ot_in = add_to_date(ot_in, hours=( entry.get('late') / 60 / 60 ))
							if ded_late_ot:
								entry['late_deduction'] = entry['late']
								entry['late'] -= ot_filed
								if entry.get('late') < 0:
									entry['late_deduction'] = ot_filed
						if entry.get('late') < 0:
							entry['late'] = 0

				#get OT Start Deduct Undertime
				if entry.get('ot_deduct_ut') and not entry.get('is_flexible') and not entry.get('dn_ot_ut'):
					if min_ot_mins > 0:
						if flt(ot_filed/60, 8) < flt(min_ot_mins, 8):
							ot_filed = 0
					if entry.get('is_restday') < 1:
						if entry.get('is_holiday'):
							if entry.get('ot_dedut_ho'):
								ot_in = add_to_date(ot_in, hours=( entry.get('undertime') / 60 / 60 ))
								if ded_ut_ot:
									entry['ut_deduction'] = entry['undertime']
									entry['undertime'] -= ot_filed
									if entry.get('undertime') < 0:
										entry['ut_deduction'] = ot_file

						else:
							ot_in = add_to_date(ot_in, hours=( entry.get('undertime') / 60 / 60 ))
							if ded_ut_ot:
								entry['ut_deduction'] = entry['undertime']
								entry['undertime'] -= ot_filed
								if entry.get('undertime') < 0:
									entry['ut_deduction'] = ot_filed

						if entry.get('undertime') < 0:
							entry['undertime'] = 0
	
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
									o['ot_out'] = o['ot_in']

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
					ot_nd = 0
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
								
						if enable_otndex:
							if ot_in and ot_nd_end:
								if ot_nd_end >= ot_in + timedelta(hours=8):
									ot_nd_end = min(ot_nd_end, ot_in + timedelta(hours=8))
	
					#Get ND OT and Calculate ND OT From Start to End
					if ot_nd_start and ot_nd_end and ot_nd_start < ot_nd_end:
						ot_nd = abs((ot_nd_start - ot_nd_end).total_seconds())
						if enable_otndex:
							if abs((ot_nd_start - ot_nd_end).total_seconds()) >= 28800:
								ot_nd = 28800

					otndbrk = 0
					ot_nd_user_brk = 0
					if nd_early_start:
						#Get early ND OT
						early_out =  None
						if ot_in < nd_early_start:
							if ot_out > nd_early_start:
								ot_nd = abs((ot_in - nd_early_start).total_seconds())
								early_out = get_datetime(nd_early_start)
							else:
								ot_nd = abs((get_datetime(ot_in) - get_datetime(ot_out)).total_seconds())
								early_out = get_datetime(ot_out)
							ot_earlynd, ot_latend = get_early_and_late_nd(entry, ot_in, ot_out, otndbrk, 1)
							if ot_earlynd:
								total_ot_earlynd += ot_earlynd
							if ot_latend:
								total_ot_latend += ot_latend

					if d.break_hrs:
						to_hrs, from_hrs, break_mins = frappe.db.get_value("Overtime Application", d['name'], ["to_hrs", "from_hrs", "break_mins"])
						if is_break_deducted != 1:
							if not from_hrs and not to_hrs and not break_mins:
								total_brk += flt(d.break_hrs, 8) * 60 * 60
								is_break_deducted = 1
							if from_hrs and to_hrs and flt(from_hrs, 8) * 60 * 60 <= ot_normal <= flt(to_hrs, 8) * 60 * 60:
								total_brk += flt(break_mins, 8) * 60
								is_break_deducted = 1

						if is_nd_break_deducted !=1:
							if flt(from_hrs, 8) * 60 * 60 <= ot_nd <= flt(to_hrs, 8) * 60 * 60:
								ot_nd -= flt(break_mins, 8) * 60
								otndbrk += flt(break_mins, 8) * 60
								is_nd_break_deducted = 1

					if entry.get('nd_start') and entry.get('nd_end'):
						nd_start = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_start')) )
						nd_end = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_end')) )
						if entry.get('nd_start') > entry.get('nd_end'):
							nd_end = get_datetime( str( add_days(entry.get('target_date'), 1) ) +" "+ str(entry.get('nd_end')) )
					
					if ot_nd_start and ot_nd_end:
						ot_earlynd, ot_latend = get_early_and_late_nd(entry, ot_nd_start, ot_nd_end, 0, 1)
						if ot_earlynd:
							total_ot_earlynd += ot_earlynd
							ot_nd_user_brk = 1
						if ot_latend:
							total_ot_latend += ot_latend
							ot_nd_user_brk = 1

					#OT ND break
					if otndbrk:
						ot_late_deduct = 0
						if ot_latend:
							ot_late_deduct =  ot_latend - otndbrk
							if ot_late_deduct >= 0:
								total_ot_latend -= otndbrk
							else: 
								total_ot_latend -= ot_latend
								total_ot_earlynd += ot_late_deduct

						else:
							if ot_earlynd:
								ot_late_deduct =  ot_earlynd - otndbrk
								if ot_late_deduct >= 0:
									total_ot_earlynd -= otndbrk
								else: 
									total_ot_earlynd -= ot_earlynd

						if total_ot_earlynd < 0:
							total_ot_earlynd = 0

					if ot_nd_user_brk == 1:
						otndbrk = 0
					total_ot_nd += ot_nd

					#Get OTNDEX
					ot_ex_start = ot_in + timedelta(hours=8)
					ot_ex_end = ot_out
					if ot_nd_start:
						ot_ndex_start = max(ot_nd_start, ot_ex_start)
						ot_ndex_end = ot_out
						total_otndex += (ot_ndex_end - ot_ndex_start).total_seconds()

				total_ot += ot_normal

		# REDUCE BREAK HRS ON REGULAR OT
		if total_brk:
			total_ot -= total_brk
			total_otndex -= total_brk
		# Deduct Late In total OT HOURS
		if entry.get('ot_deduct_late') and not entry.get('is_flexible') and entry.get('dn_ot_late') and not entry['is_holiday']:
			if min_ot_mins > 0:
				if flt(total_ot/60, 8) < flt(min_ot_mins, 8):
					total_ot = 0

				if flt(total_ot_nd/60, 8) < flt(min_ot_mins, 8):
					total_ot_nd = 0
					
			if entry.get('is_restday') < 1:
				total_ot_deducted = total_ot
				if entry.get('is_holiday'):
					if entry.get('ot_dedlt_ho'):
						total_ot -= entry['late']
						total_ot_nd -= entry['late']
						total_ot_latend -= entry['late']
						if total_ot_latend < 0:
							total_ot_earlynd -= abs(total_ot_latend)
							total_ot_latend = 0
							if  total_ot_earlynd < 0:
								total_ot_earlynd = 0
						if total_ot < 0:
							total_ot = 0
						if total_ot_nd < 0:
							total_ot_nd = 0

						total_ot_deducted -= total_ot
						if ded_late_ot:
							entry['late'] -= total_ot_deducted
				else:
					total_ot_nd -= entry['late']
					total_ot -= entry['late']
					total_ot_latend -= entry['late']
					if total_ot_latend < 0:
						total_ot_earlynd -= abs(total_ot_latend)
						total_ot_latend = 0
						if  total_ot_earlynd < 0:
							total_ot_earlynd = 0
					if total_ot < 0:
						total_ot = 0
					if total_ot_nd < 0:
						total_ot_nd = 0
					total_ot_deducted -= total_ot
					if ded_late_ot:
						entry['late'] -= total_ot_deducted
				if entry.get('late') < 0:
					entry['late'] = 0
				entry['late_deduction'] = total_ot_deducted

		# Deduct Undertime In total OT HOURS
		if entry.get('ot_deduct_ut') and not entry.get('is_flexible') and entry.get('dn_ot_ut') and not entry['is_holiday']:
			if min_ot_mins > 0:
				if flt(total_ot/60, 8) < flt(min_ot_mins, 8):
					total_ot = 0

				if flt(total_ot_nd/60, 8) < flt(min_ot_mins, 8):
					total_ot_nd = 0
					
			if entry.get('is_restday') < 1:
				total_ot_deducted = total_ot
				if entry.get('is_holiday'):
					if entry.get('ot_dedut_ho'):
						total_ot -= entry['undertime']
						total_ot_nd -= entry['undertime']
						total_ot_latend -= entry['undertime']
						if total_ot_latend < 0:
							total_ot_earlynd -= abs(total_ot_latend)
							total_ot_latend = 0
							if  total_ot_earlynd < 0:
								total_ot_earlynd = 0
						if total_ot < 0:
							total_ot = 0
						if total_ot_nd < 0:
							total_ot_nd = 0

						total_ot_deducted -= total_ot
						if ded_ut_ot:
							entry['undertime'] -= total_ot_deducted
				else:
					total_ot_nd -= entry['undertime']
					total_ot -= entry['undertime']
					total_ot_latend -= entry['undertime']
					if total_ot_latend < 0:
						total_ot_earlynd -= abs(total_ot_latend)
						total_ot_latend = 0
						if  total_ot_earlynd < 0:
							total_ot_earlynd = 0
					if total_ot < 0:
						total_ot = 0
					if total_ot_nd < 0:
						total_ot_nd = 0
					total_ot_deducted -= total_ot
					if ded_ut_ot:
						entry['undertime'] -= total_ot_deducted
				if entry.get('undertime') < 0:
					entry['undertime'] = 0
				entry['ut_deduction'] = total_ot_deducted

		#Minimum OT (Mins)
		min_ot_mins = frappe.db.get_single_value('Timekeeping Settings', 'min_ot_mins')
		if min_ot_mins > 0:
			if flt(total_ot/60, 8) < flt(min_ot_mins, 8):
				total_ot = 0

			if flt(total_ot_nd/60, 8) < flt(min_ot_mins, 8):
				total_ot_nd = 0

			if flt(total_otndex/60, 8) < flt(min_ot_mins, 8):
				total_otndex = 0

		if total_ot < 0:
			total_ot = 0

		if total_ot_nd < 0:
			total_ot_nd = 0

		if total_otndex < 0:
			total_otndex = 0

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
			if ded_brk_otreg and total_brk:
				total_ot_nd -= total_brk

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
				'early_nd': total_ot_earlynd / 60 / 60,
				'late_nd': total_ot_latend / 60 / 60,
				#"linked_ot": d.name,
				"ot_tag": "",
			})
			entry['overtime_nd'] = total_ot_nd
			entry['ot_early_nd'] = total_ot_earlynd
			entry['ot_late_nd'] = total_ot_latend

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

		#GET OTNDEX
		if enable_otndex and total_otndex:
			ot_ex_code = [entry.get('is_restday'), entry.get('is_holiday'), entry.get('is_sp_holiday'), is_db_holiday, is_sunday, is_saturday, 1, 1]
			ot_ex_code = ''.join(str(x) for x in ot_ex_code)
			ot_list.append({
				"employee": entry.get('employee'),
				"target_date": entry.get('target_date'),
				"ot_type": "OTNDEX",
				"ot_code": ot_ex_code,
				"ot_hrs": total_otndex / 60 / 60,
				#"linked_ot": d.name,
				"ot_tag": "",
			})
			entry['overtime_ndex'] = total_otndex

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

	if entry.get('nd_start') and entry.get('nd_end') and not frappe.db.get_value("Employee", entry['employee'], "ignore_nd") and not entry['is_restday']:
		#get ND start and end
		nd_early_start, nd_early_end = None, None
		nd_start, nd_end  = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_start')) ), get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_end')) )
		if entry.get('nd_start') > entry.get('nd_end'):
			nd_end = get_datetime( str( add_days(entry.get('target_date'), 1) ) +" "+ str(entry.get('nd_end')) )
			nd_early_start = get_datetime( str( entry.get('target_date') ) +" 00:00:00" )
			nd_early_end = get_datetime( str( entry.get('target_date') ) +" "+ str(entry.get('nd_end')) )

		#set min ND and max ND
		min_nd, max_nd, nd_pro  = entry.get('nd_start'),  entry.get('nd_end'), 1

		card_in = entry.get('card_in')
		card_out = entry.get('card_out')
		ded_late_ot = frappe.db.get_single_value('Timekeeping Settings', 'ded_late_ot')
		ded_ut_ot = frappe.db.get_single_value('Timekeeping Settings', 'ded_ut_ot')

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

		#Get ND late with interval
		nd_late = abs((get_datetime(card_in)- get_datetime(entry["time_in"])).total_seconds())
		if entry['is_flexible'] and entry['flexible_type'] != "In-Out":

			flex_start = entry.get('card_in')
			flex_end = entry.get('card_out')
			if entry.get('ob_stat') == 1:
				if entry['card_in']:
					if entry.get('ob_in') < entry.get('card_in'):
						flex_start = entry.get('ob_in')
				if entry['card_out']:
					if entry.get('ob_out') > entry.get('card_out'):
						flex_end = entry.get('ob_out')

			late_point = get_datetime( str(entry.get('target_date'))+" "+ str(entry.get('flex_to')))
			if late_point and flex_start:
				if flex_start > late_point:
					if entry.get('grace'):
						if flex_start > (late_point + datetime.timedelta(minutes=entry.get('grace'))):
							if entry['graceperiod_late']:
									#late computaion will start from grace period
								entry['late'] = ( flex_start - (late_point + datetime.timedelta(minutes=entry.get('grace'))) ).total_seconds()
								flex_start = late_point
							else:
								entry['late'] = (flex_start - late_point).total_seconds()
								flex_start = late_point

						else:
							#late computaion will start from flex start
							entry['late'] = 0
							flex_start = late_point

					else:
						entry['late'] = (flex_start - late_point ).total_seconds()
						flex_start = late_point

					if entry['late_interval'] and entry.get('late'):
						if entry.get('lt_int_rup'):
							lt_start = entry.get('late_interval') * 60
							lt_end = entry.get('late_interval') * 60
							while entry['late'] != lt_end:
								if entry['late'] <= lt_start:
									entry['late'] = lt_start
									break
								if lt_start < entry.get('late') <= lt_end:
									entry['late'] = lt_end
									break
								lt_start = lt_end
								lt_end += entry.get('late_interval') * 60
						else:
							entry['late'] = (entry.get('late_interval') * 60) * int( entry['late'] / (entry.get('late_interval') * 60))
						flex_start = add_to_date(get_datetime(late_point), hours=((entry['late'] /60 / 60)))
					card_in = flex_start

		elif entry['late_interval'] and entry.get('late') and not entry['is_flexible']:
			if entry.get('lt_int_rup'):
				lt_start = entry.get('late_interval') * 60
				lt_end = entry.get('late_interval') * 60
				while nd_late != lt_end:
					if nd_late <= lt_start:
						nd_late = lt_start
						break
					if lt_start < entry.get('late') <= lt_end:
						nd_late = lt_end
						break
					lt_start = lt_end
					lt_end += entry.get('late_interval') * 60
			else:
				nd_late = (entry.get('late_interval') * 60) * int( nd_late / (entry.get('late_interval') * 60))
			card_in = add_to_date(get_datetime(entry["time_in"]), hours=((nd_late /60 / 60)))


		#check shift if eligible for nightdiff based from time in and time out:
		min_nd, max_nd, nd_pro = get_ndiff_min_max(nd_start, nd_end, entry.get('time_out'), entry.get('time_in'))
		if entry.get('ot_deduct_late') and not entry.get('is_flexible') and entry['late_deduction']:
			if entry.get('is_restday') < 1:
				if ded_late_ot:
					card_in = add_to_date(get_datetime(card_in), hours=( -(entry['late_deduction']/60/60)))

				if card_in < entry.get('time_in'):
					card_in = entry['time_in']
				
		if card_in and card_out and nd_pro == 1:
			nd_in, nd_out, get_nd = get_ndiff_min_max(min_nd, max_nd, card_out, card_in)
			if get_nd:
				entry['nightdiff'] = abs((nd_out - nd_in).total_seconds())
				if not entry['is_holiday']:
					entry['earlynightdiff'], entry['latenightdiff'] = get_early_and_late_nd(entry, nd_in, nd_out)

		#early nightdiff No need for early nightdiff ND should be insided shift
		if card_in and card_out:
			if nd_early_start and nd_early_end:
				if nd_early_start <= entry.get('time_in') <= nd_early_end:
					nd_in, nd_out, get_nd = get_ndiff_min_max(min_nd, max_nd, card_out, card_in)
					employee_nd_early_start = nd_early_start
					if getdate(entry.get('time_in')) == getdate(entry.get("target_date")):
						employee_nd_early_start = max(nd_early_start, entry.get('time_in'))
					employee_nd_early_end = min(nd_early_end, entry.get('time_out'))
					entry['early_nightdiff'] = 0
					entry['early_nightdiff'] = (abs(( get_datetime(employee_nd_early_end) - employee_nd_early_start ).total_seconds()))
					entry['nightdiff'] += entry['early_nightdiff']

			nd_early_start = get_datetime(str(entry.get('target_date')) +" "+ str(entry.get('nd_end')) )
			if entry.get('time_in') <= nd_early_start:
				if get_datetime(entry.get('card_in')) < nd_early_start:
					if get_datetime(entry.get('card_in')) < get_datetime(entry.get('time_in')):
						if not entry['is_holiday']:
							early_diff, late_diff = get_early_and_late_nd(entry, entry['time_in'], nd_early_start)
							if early_diff:
								entry['earlynightdiff'] += early_diff
							if late_diff:
								entry['latenightdiff'] += late_diff					

	return entry

def get_early_and_late_nd(entry, nd_in, nd_out, brk_hrs=None, from_ot=0):
	#Get ND Rate Class
	earlynightdiff, latenightdiff = 0, 0
	end_in, end_out, lnd_in, lnd_out = None, None, None, None
	end_hrs, lnd_hrs = 0, 0
	today_end_in = get_datetime(str(entry.get('target_date')) +" 00:00")
	today_end_out = get_datetime(str(entry.get('target_date')) +" 06:00")
	rc_end_in = get_datetime(str(entry.get('target_date')) +" 22:00")
	rc_end_out = get_datetime(str(add_days(getdate(entry['target_date']), 1)) +" 06:00")
	rc_lnd_in = get_datetime(str(entry.get('target_date')) +" 18:00")
	rc_lnd_out = get_datetime(str(entry.get('target_date')) +" 22:00")
	
	#if from_ot and nd_in < rc_end_in:
	#	rc_end_in = get_datetime(str(add_days(getdate(entry['target_date']), -1)) +" 22:00")
	#	rc_end_out = get_datetime(str(entry.get('target_date')) +" 06:00")

	#END
	if (nd_in <= rc_end_in <= nd_out) or (nd_in <= rc_end_out <= nd_out):
		if nd_in < rc_end_in:
			end_in = rc_end_in
		if nd_in >= rc_end_in:
			end_in = nd_in

		if nd_out <= rc_end_out:
			end_out = nd_out
		if nd_out > rc_end_out:
			end_out = rc_end_out

	elif (rc_end_in <= nd_in <= rc_end_out) or (rc_end_in <= nd_out <= rc_end_out):
		if nd_in < rc_end_in:
			end_in = rc_end_in
		if nd_in >= rc_end_in:
			end_in = nd_in

		if nd_out <= rc_end_out:
			end_out = nd_out
		if nd_out > rc_end_out:
			end_out = rc_end_out

	if end_in and end_out:
		earlynightdiff = abs(( end_out - end_in ).total_seconds())

	#Today END
	end_in, end_out = None, None
	if (nd_in <= today_end_in <= nd_out) or (nd_in <= today_end_out <= nd_out):
		if nd_in < today_end_in:
			end_in = today_end_in
		if nd_in >= today_end_in:
			end_in = nd_in

		if nd_out <= today_end_out:
			end_out = nd_out
		if nd_out > today_end_out:
			end_out = today_end_out

	elif (today_end_in <= nd_in <= today_end_out) or (today_end_in <= nd_out <= today_end_out):
		if nd_in < today_end_in:
			end_in = today_end_in
		if nd_in >= today_end_in:
			end_in = nd_in

		if nd_out <= today_end_out:
			end_out = nd_out
		if nd_out > today_end_out:
			end_out = today_end_out

	if end_in and end_out:
		earlynightdiff += abs(( end_out - end_in ).total_seconds())

	#LND
	if (nd_in <= rc_lnd_in <= nd_out) or (nd_in <= rc_lnd_out <= nd_out):
		if nd_in < rc_lnd_in:
			lnd_in = rc_lnd_in
		if nd_in >= rc_lnd_in:
			lnd_in = nd_in

		if nd_out <= rc_lnd_out:
			lnd_out = nd_out
		if nd_out > rc_lnd_out:
			lnd_out = rc_lnd_out

	elif (rc_lnd_in <= nd_in <= rc_lnd_out) or (rc_lnd_in <= nd_out <= rc_lnd_out):
		if nd_in < rc_lnd_in:
			lnd_in = rc_lnd_in
		if nd_in >= rc_lnd_in:
			lnd_in = nd_in

		if nd_out <= rc_lnd_out:
			lnd_out = nd_out
		if nd_out > rc_lnd_out:
			lnd_out = rc_lnd_out

	if lnd_in and lnd_out:
		latenightdiff = abs(( lnd_out - lnd_in ).total_seconds())

	if brk_hrs:
		if latenightdiff:
			latenightdiff =  latenightdiff - brk_hrs

			if latenightdiff < 0:
				if earlynightdiff:
					earlynightdiff -= latenightdiff
				latenightdiff = 0
		else:
			if earlynightdiff:
				earlynightdiff =  earlynightdiff - brk_hrs

		if earlynightdiff < 0:
			earlynightdiff = 0

	return earlynightdiff, latenightdiff

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

	entry['late_without_int'] = entry['late'] 
	if entry.get('late_interval'):
		if entry.get('lt_int_rup'):
			if entry.get('late'):
				lt_start = entry.get('late_interval') * 60
				lt_end = entry.get('late_interval') * 60
				while entry.get('late') != lt_end:
					if entry.get('late') <= lt_start:
						entry['late'] = lt_start
						break
					if lt_start < entry.get('late') <= lt_end:
						entry['late'] = lt_end
						break
					lt_start = lt_end
					lt_end += entry.get('late_interval') * 60
		else:
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
		start, end = entry['ut_from'], entry['ut_to']
		has_undertime = 0
		
		if entry['card_in'] and entry['card_out'] or entry['ob_stat']:
			if not get_datetime(start) >= get_datetime(entry['time_out']) and not get_datetime(end) <= get_datetime(entry['time_in']) and not get_datetime(start) >= get_datetime(end):
				for ut in entry['ut_list']:
					if get_datetime(entry['ut_from']) < get_datetime(entry["time_in"]):
						start =  get_datetime(entry["time_in"])

					if get_datetime(entry['ut_to']) > get_datetime(entry["time_out"]):
						end =  get_datetime(entry["time_out"])

					if get_datetime(ut['to_time']) == get_datetime(entry['break_start']):
						end =  get_datetime(entry["break_start"])
					if not get_datetime(ut['from_time']) > get_datetime(end) and not get_datetime(ut['to_time']) < get_datetime(start) and not  get_datetime(ut['to_time']) == get_datetime(entry['break_end']):
						current_ut = abs((ut['to_time'] - ut['from_time']).total_seconds())
						
						if get_datetime(ut['from_time']) < get_datetime(start):
							start = ut['from_time'] 

						if get_datetime(ut['to_time']) > get_datetime(end):
							end = ut['to_time']
							
						new_ut = abs((end - start).total_seconds())
						additional_undertime += abs(new_ut - current_ut)
					if get_datetime(ut['from_time']) == get_datetime(start) and get_datetime(ut['to_time']) == get_datetime(end):
						has_undertime = 1

		if additional_undertime == 0 and has_undertime == 0:
			if not (get_datetime(start) >= get_datetime(entry['time_out']) or get_datetime(end) <= get_datetime(entry['time_in']) or get_datetime(start) >= get_datetime(end)):
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
			break_has_deducted = 0
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
						cto_logs = []
						cto_logs.append({"start": ct['start'], "end": ct['end']})

						if entry["late"] or entry["late_list"]:
							for l in entry["late_list"]:
								start, end = None, None
								cto = 0
								late = entry["late"]
								if not (entry['is_flexible'] and entry.get('flexible_type') == "In-Out"):
									if not (ct['start'] >= l['to_time'] or ct['end'] <= l['from_time']):
										if ct['start'] > l['from_time']:
											start = ct['start']
										else:
											start = l['from_time']
										if ct['end'] < l['to_time']:
											end = ct['end']
										else:
											end = l['to_time']
										entry['cto'] += abs((start - end).total_seconds())
									elif entry['is_flexible'] and entry.get('flexible_type') == "Standard":
										if ct['end'] > entry['time_out']:
											cto += abs((ct['end'] - entry['time_out']).total_seconds())
										if cto > entry["late"]:
											entry['cto'] += entry["late"]
										if cto <= entry["late"]:
											entry['cto'] += cto

						if entry["undertime"] or entry["ut_list"]:
							ut_start = None
							ut_end = None

							for u in entry["ut_list"]:
								if not ut_start:
									ut_start = u['from_time']
									ut_end = u['to_time']
								else:
									if not (ut_start > u['to_time'] or ut_end < u['from_time']):
										if ut_start <= u['from_time'] < ut_end < u['to_time']:
											u['from_time'] = ut_end
										if u['from_time'] <= ut_start < u['to_time'] < ut_end:
											u['to_time'] = ut_start

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

							if entry['is_flexible']:
								late_point = get_datetime( str(entry.get('target_date'))+" "+ str(entry.get('flex_to')) )
								if entry.get('flexible_type') == "In-Out":
									for f in entry['flex_in_out']:
										for cl in cto_logs:
											if get_datetime(cl['start']) < get_datetime(f['from_time']) or get_datetime(cl['end']) > get_datetime(f['to_time']):
												if get_datetime(cl['start']) < get_datetime(f['from_time']):
													if get_datetime(cl['end']) > get_datetime(f['from_time']):
														if get_datetime(cl['end']) > get_datetime(f['to_time']):
															cl['end'] = f['from_time']
															cto_logs.append({"start":f['to_time'] , "end": cl['end']})
														else:
															cl['end'] = f['from_time']
												elif get_datetime(cl['end']) > get_datetime(f['to_time']):
													if get_datetime(cl['start']) < get_datetime(f['to_time']):
														cl['start'] = f['to_time']
								else:
									for cl in cto_logs:
										if get_datetime(cl['end']) > get_datetime(late_point):
											if get_datetime(cl['start']) < get_datetime(late_point):
												cl['start'] = late_point
											if entry['flex_in_out']:
												for f in entry['flex_in_out']:
													if get_datetime(cl['end']) > get_datetime(f['to_time']):
														if get_datetime(cl['start']) < get_datetime(f['to_time']):
															cl['start'] = f['to_time']
														if get_datetime(cl['end']) > get_datetime(entry['time_out']):
															cl['end'] = entry['time_out']
													else:
														cl['end'] = cl['start']
										else:
											cl['end'] = cl['start']
								for c in cto_logs:
									entry['cto'] += abs((c['start'] - c['end']).total_seconds())

						if entry["is_absent"]:
							if entry['is_flexible']:
								for c in cto_logs:
									entry['cto'] += abs((c['start'] - c['end']).total_seconds())
								if entry['cto']:
									if entry['cto'] > entry['worker_secs']:
										entry['cto'] = entry['worker_secs']

							else:
								if (cto_fromtime <= entry.get('time_in') <= cto_totime) or (cto_fromtime <= entry.get('time_out') <= cto_totime)\
								or (entry.get('time_in') <= cto_fromtime <= entry.get('time_out')) or (entry.get('time_in') <= cto_totime <= entry.get('time_out')):
#									entry['cto'] = d.use_total_hours * 60 * 60
#									if d.use_total_hours * 60 * 60 > entry['work_hours']:
#										entry['cto'] = entry['work_hours'] * 60 * 60

									ctofrom = cto_fromtime
									ctoto = cto_totime
									total_cto_hours = abs((ctofrom - ctoto).total_seconds())
									if cto_fromtime < entry.get('time_in'):
										ctofrom = entry.get('time_in')
									if cto_totime > entry.get('time_out'):
										ctoto = entry.get('time_out')
									entry['cto'] += abs((ctofrom - ctoto).total_seconds())
									deducted_break = abs(total_cto_hours - entry['cto'])
									d.break_hours = ((d.break_hours) * 60 * 60) - deducted_break
									d.break_hours = d.break_hours / 60 / 60
									if d.break_hours  < 0:
										d.break_hours = 0		

#									breakin = None
#									breakout = None
#									if (ctofrom <= entry.get('break_start') <= ctoto):
#										breakin = entry.get('break_start')
#									if (ctofrom <= entry.get('break_end') <= ctoto):
#										breakout = entry.get('break_end')
#									if breakin and breakout:
#										entry['cto'] -= abs((breakin - breakout).total_seconds())

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

								if entry['cto']:
									entry['cto'] -= flt(d.break_hours, 2) * 60 * 60
									if entry['cto'] > entry['work_hours'] * 60 * 60:
										entry['cto'] = entry['work_hours'] * 60 * 60
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
		entry["late_list"] = []
		entry["ut_list"] = []

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
			entry['flex_in_out'].append({"from_time":  entry.get('ob_in') , "to_time": entry.get('ob_out')})

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
						if entry.get('ut_interval'):
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

					entry['flex_in_out'].append({"from_time":  entry.get('card_in'), "to_time": entry.get('card_in')})
					entry['late'] = 0
					entry['undertime'] = ut
					entry['work'] = entry.get('worker_secs') - (ut + lv)
			else:
				#gete late base from flexible start time
				flex_start = entry.get('card_in')
				flex_end = entry.get('card_out')
				nd_late = abs((get_datetime(flex_start)- get_datetime(entry["time_in"])).total_seconds())

				if entry.get('ob_stat') == 1:
					if entry.get('ob_in') < entry.get('card_in'):
						flex_start = entry.get('ob_in')

					if entry.get('ob_out') > entry.get('card_out'):
						flex_end = entry.get('ob_out')
				#late point if the flex start is beyond this point consider as late.
				late_point = get_datetime( str(entry.get('target_date'))+" "+ str(entry.get('flex_to')) )

				#calculate late
				entry['flex_in_out'].append({"from_time":  entry.get('card_in'), "to_time": entry.get('card_in')})
				if late_point:
					if flex_start > late_point:
						if entry.get('grace'):
							if flex_start > (late_point + datetime.timedelta(minutes=entry.get('grace'))):
								if entry['graceperiod_late']:
									#late computaion will start from grace period
									entry['late'] = ( flex_start - (late_point + datetime.timedelta(minutes=entry.get('grace'))) ).total_seconds()
									entry['late_list'].append({'from_time': late_point + datetime.timedelta(minutes=entry.get('grace')), 'to_time': flex_start})
									flex_start = late_point
								else:
									#late computaion will start from flex start
									entry['late'] = ( flex_start - (late_point) ).total_seconds()
									entry['late_list'].append({'from_time': late_point, 'to_time': flex_start})
									flex_start = late_point
							else:
								#if there is no late computed with grace period, set flex start to late point
								flex_start = late_point
						else:
							if entry.get('late_interval'):
								nd_late = (entry.get('late_interval') * 60) * int( nd_late / (entry.get('late_interval') * 60))
							entry['late'] = (flex_start - late_point ).total_seconds()
							entry['late_list'].append({'from_time': late_point, 'to_time': flex_start})
							flex_start = late_point

				if get_datetime(flex_end) >= get_datetime(entry.get('break_end')):
					diff_break = entry.get('break_mins') * 60
				#always reduce break mins
				diff = abs( (flex_start - flex_end).total_seconds())  - (diff_break) + flex_ob_time

				entry['flex_in_out'].append({"from_time":  flex_start, "to_time": flex_end})
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
				if entry['late']:
					if entry.get('late_interval'):
						if entry.get('lt_int_rup'):
							if entry.get('late'):
								lt_start = entry.get('late_interval') * 60
								lt_end = entry.get('late_interval') * 60
								while entry.get('late') != lt_end:
									if entry.get('late') <= lt_start:
										entry['late'] = lt_start
										break
									if lt_start < entry.get('late') <= lt_end:
										entry['late'] = lt_end
										break
									lt_start = lt_end
									lt_end += entry.get('late_interval') * 60
						else:
							entry['late'] = (entry.get('late_interval') * 60) * int( entry['late'] / (entry.get('late_interval') * 60))
					entry['work'] -= entry['late']

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
					if entry.get('ut_interval'):
						ut = (entry.get('ut_interval') * 60) * int( ut / (entry.get('ut_interval') * 60))
					if (entry.get('lv_status') == 2 and entry.get('ob_stat') == 3) or (entry.get('lv_status') == 3 and entry.get('ob_stat') == 2):
						entry['work'] = entry['work'] / 2
						ut = 0
					else:
						entry['undertime'] = ut
						entry['work'] = entry.get('worker_secs')  - ut

		#Work should not be greater than assigned work hrs
		if entry['work'] > entry.get('worker_secs'):
			entry['work'] = entry.get('worker_secs')
			entry['undertime'] = 0

def get_final_processing(entry):
	if entry['is_multi_break'] and entry.get('is_attendance_base'):
		total_break = 0
		entry['break_out'] = min(entry['break_pairs'])['break_out'] if entry['break_pairs'] else None
		entry['break_in'] = max(entry['break_pairs'])['break_in'] if entry['break_pairs'] else None

		if entry['break_pairs']:
			for break_pair in entry['break_pairs']:
				total_break += break_pair['break_mins'] * 60
		entry['break'] = total_break

		if entry['max_break'] > 0:
			if total_break > (entry['max_break'] * 60):
				entry["undertime"] = total_break - (entry['max_break'] * 60)
				entry['excess_break'] = total_break - (entry['max_break'] * 60)

		if not entry['card_in'] or not entry['card_out']:
			entry['break'] = 0
			entry["undertime"] = 0
			entry['excess_break'] = 0

		if entry['undertime']:
			entry['work'] -= entry['undertime']
	
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
								entry['late_list'].append({'from_time': lt['from_time'], 'to_time': et['from_time']})
	
							if lt.get('to_time') < et.get('to_time'):
								exc_end = get_datetime(lt['to_time'])
							else: 
								exc_end = get_datetime(et['to_time'])
								entry['late_list'].append({'from_time': et['from_time'], 'to_time': lt['from_time']})

							entry['late_list'].remove(lt)
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
								entry['ut_list'].append({'from_time': ut['from_time'], 'to_time': et['from_time']})
	
							if ut.get('to_time') < et.get('to_time'):
								exc_end = get_datetime(ut['to_time'])
							else: 
								exc_end = get_datetime(et['to_time'])
								entry['ut_list'].append({'from_time': et['from_time'], 'to_time': ut['from_time']})
							entry['ut_list'].remove(ut)
	
							entry['undertime'] -= abs((exc_end - exc_start).total_seconds())
							if entry['undertime'] < 0:
								entry['undertime'] = 0
		#suspension
		if entry['suspension'] == 1:
			entry['undertime'] = 0
			entry['late'] = 0
		if entry['suspension'] == 2:
			for lt in entry['late_list']:
				if get_datetime(entry['time_in']) <= get_datetime(lt['from_time']) and get_datetime(entry['break_end']) >= get_datetime(lt['to_time']):
					if get_datetime(lt['to_time']) > get_datetime(entry['break_start']):
						lt['to_time'] = entry['break_start']
					entry['late'] -= abs((lt['to_time'] - lt['from_time']).total_seconds())
			for ut in entry['ut_list']:
				if get_datetime(entry['time_in']) <= get_datetime(ut['from_time']) and get_datetime(entry['break_end']) >= get_datetime(ut['to_time']):
					if get_datetime(ut['to_time']) > get_datetime(entry['break_start']):
						ut['to_time'] = entry['break_start']
					entry['undertime'] -= abs((ut['to_time'] - ut['from_time']).total_seconds())
		if entry['suspension'] == 3:
			for lt in entry['late_list']:
				if get_datetime(entry['break_end']) <= get_datetime(lt['from_time']) and get_datetime(entry['time_out']) >= get_datetime(lt['to_time']):
					entry['late'] -= abs((lt['to_time'] - lt['from_time']).total_seconds())
			for ut in entry['ut_list']:
				if get_datetime(entry['break_end']) <= get_datetime(ut['from_time']) and get_datetime(entry['time_out']) >= get_datetime(ut['to_time']):
					entry['undertime'] -= abs((ut['to_time'] - ut['from_time']).total_seconds())

	
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
	lt_job_grade = frappe.db.sql(""" SELECT JGT.`job_grade`, JGT.`lt_value` FROM `tabJob Grade Table` JGT INNER JOIN `tabEmployee` E ON E.`job_grade` = JGT.`job_grade` WHERE E.name = %s """,(entry['employee']), as_dict=1) 
	 
	 
	if lt_job_grade: 
		for j in lt_job_grade: 
			if flt(entry["late"], 8) >= int(j['lt_value']) and int(j['lt_value']) > 0 and entry.get('lv_status') != 2 and entry.get('lv_status') != 1 and not entry.get('is_restday') and not entry['is_holiday']: 
				entry["late"] = 0 
				entry["absent"] = 1 
				entry["is_halfday"] = 1
				entry['actual_work'] = entry['work']
				if not frappe.db.get_single_value('Timekeeping Settings', 'hd_actualwork'):
					entry['work'] = (entry.get('work_hours') * 60 * 60) / 2
				ch_tr=1 
 
	if not lt_job_grade: 
		if flt(entry["late"], 8) >= ch and ch > 0 and entry.get('lv_status') != 2 and entry.get('lv_status') != 1 and not entry.get('is_restday') and not entry['is_holiday']:		 
			entry["late"] = 0 
			entry["absent"] = 1 
			entry["is_halfday"] = 1
			entry['actual_work'] = entry['work']
			if not frappe.db.get_single_value('Timekeeping Settings', 'hd_actualwork'):
				entry['work'] = (entry.get('work_hours') * 60 * 60) / 2
			ch_tr=1 
 
	chu_tr=0 
	chu = flt(frappe.db.get_single_value('Timekeeping Settings', 'ut_consider_halfday'), 8) 
	ut_job_grade = frappe.db.sql(""" SELECT JGT.`job_grade`, JGT.`ut_value` FROM `tabJob Grade Table` JGT INNER JOIN `tabEmployee` E ON E.`job_grade` = JGT.`job_grade` WHERE E.name = %s """,(entry['employee']), as_dict=1) 
	 
	if ut_job_grade: 
		for j in ut_job_grade: 
			if flt(entry["undertime"], 8) >= int(j['ut_value']) and int(j['ut_value'])  > 0 and entry.get('lv_status') != 3 and entry.get('lv_status') != 1 and not entry.get('is_restday') and not entry['is_holiday']:		 
				entry["undertime"] = 0		 
				entry["absent"] = 1		 
				entry["is_halfday"] = 1
				entry['actual_work'] = entry['work']
				if not frappe.db.get_single_value('Timekeeping Settings', 'hd_actualwork'):
					entry['work'] = (entry.get('work_hours') * 60 * 60) / 2
				chu_tr=1 
					 
	if not ut_job_grade:				 
		if flt(entry["undertime"], 8) >= chu and chu > 0 and entry.get('lv_status') != 3 and entry.get('lv_status') != 1 and not entry.get('is_restday') and not entry['is_holiday']:		 
			entry["undertime"] = 0		 
			entry["absent"] = 1		 
			entry["is_halfday"] = 1
			entry['actual_work'] = entry['work']
			if not frappe.db.get_single_value('Timekeeping Settings', 'hd_actualwork'):
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

		if entry.get('card_in') and (not entry.get('card_out')) and (not entry.get('ob_stat')):
			entry["work"] = 0
			entry["undertime"] = 0
			entry["is_absent"] = 1
			if entry.get('suspension') != 3:
				entry["late"] = 0
				
			if entry.get('hd_halfcard') and entry.get('suspension') != 3:
				entry['is_absent'] = 1
				entry["is_halfday"] = 1
				entry['actual_work'] = entry['work']
				if not frappe.db.get_single_value('Timekeeping Settings', 'hd_actualwork'):
					entry["work"] = (entry.get('work_hours') * 60 * 60) / 2
				else:
					entry["work"] = 0
				entry["late"] = 0
				entry["undertime"] = 0
		
		if entry.get('card_out') and (not entry.get('card_in')) and (not entry.get('ob_stat')):
			entry["work"] = 0
			entry["late"] = 0
			entry["is_absent"] = 1
			if entry.get('suspension') != 2:
				entry["undertime"] = 0

			if entry.get('hd_halfcard') and entry.get('suspension') != 2:
				entry['is_absent'] = 1
				entry["is_halfday"] = 1
				entry['actual_work'] = entry['work']
				if not frappe.db.get_single_value('Timekeeping Settings', 'hd_actualwork'):
					entry["work"] = (entry.get('work_hours') * 60 * 60) / 2
				else:
					entry["work"] = 0
				entry["late"] = 0
				entry["undertime"] = 0

	ws_pho = frappe.db.get_single_value('Payroll Settings', 'ws_pho')
	if ws_pho:
		if entry.get('lv_status') == 2 and entry.get('suspension') == 3:
			entry["is_halfday"] = 1
			entry["is_absent"] = 0
		if entry.get('lv_status') == 3 and entry.get('suspension') == 2:
			entry["is_halfday"] = 1
			entry["is_absent"] = 0

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

	entry['actual_work'] = entry['work']

	return entry

def get_tags(entry):
	#Timlogs Override tags
	if entry['has_timelog_override']:
		entry["tags"] += "<span class='label label-success'>Timelogs Override</span>"

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
		allow_ut_tag = 1
		if frappe.db.get_value("Employee", entry['employee'], "ignore_ut") and frappe.db.get_single_value('Timekeeping Settings', 'disable_ut_tag'):
			allow_ut_tag =0
		if allow_ut_tag:
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
	entry["tags"] += " <span class='label label-danger'> Late </span> " if entry['late'] > 0 and not frappe.db.get_single_value('Timekeeping Settings', 'disable_lt_tag') else ""
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

	for d in entry.get('tla_links'):
		entry["links"] += "<span class='label label-success'><a href='/desk#Form/Timelogs Application/"+d+"'> "+d+" </a></span>"

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

def get_period_from_targetdate(employee, target_date):
	period = None
	if frappe.db.get_single_value('Timekeeping Settings', 'cur_period_attendance_summary'):
		employee = frappe.db.sql(""" SELECT `name`, `user_id`, `company`, `payroll_schedule`, `period_group` FROM `tabEmployee` 
			WHERE `name` = %s LIMIT 1""",( employee ), as_dict=1)

		if employee:
			periods = frappe.db.sql("""SELECT `name`, `period_group` FROM `tabPayroll Period` WHERE
				(%(date_today)s BETWEEN `attendance_from` AND `attendance_to`) 
				AND `company` = %(company)s AND `schedule` = %(schedule)s """,{ 
					"date_today": getdate(target_date),
					"company": employee[0].company,
					"schedule": employee[0].payroll_schedule,
					"period_group": employee[0].period_group
				}, as_dict=True)
			if periods:
				for per in periods:
					if per.period_group:
						if employee[0].period_group and employee[0].period_group == per.period_group:
							period = per.name
					else:
						period = per.name

	return period

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

def get_actual_logs(employee, pay_from, pay_to, ot_app = None):
	result = []	
	shift_map = get_shift_map()
	template_map = get_template_map()

	emp = frappe.get_doc('Employee', employee)
	emp_map = frappe._dict()
	emp_map.setdefault(employee, frappe._dict({
			"employee": employee,
			"employee_name": emp.full_name,
			"company": emp.company,
			"employee_details": emp.__dict__,
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
			"tla": [],
			"timelogs_map": {},
		})
	)

	approval_cutoff = None
	period = get_period_from_targetdate(employee, pay_from)
	if period:
		period_disable_straight_shift, approval_cutoff = frappe.db.get_value("Payroll Period", period, ["disable_straight_shift", "approval_cutoff"] )

	get_all_schedules(emp_map, employee, pay_from - datetime.timedelta(days=3), pay_to + datetime.timedelta(days=3))
	get_all_timecards(emp_map, employee, pay_from - datetime.timedelta(days=3), pay_to + datetime.timedelta(days=3))
	get_all_csa(emp_map, employee, pay_from - datetime.timedelta(days=3), pay_to + datetime.timedelta(days=3), approval_cutoff, 1, 0)
	get_all_dtrp(emp_map, employee, pay_from - datetime.timedelta(days=3), pay_to + datetime.timedelta(days=3), approval_cutoff, 1, 0)
	get_all_tla(emp_map, employee, pay_from - datetime.timedelta(days=3), pay_to + datetime.timedelta(days=3), approval_cutoff, 1)

	complete_sched(emp_map[employee], pay_from - datetime.timedelta(days=3), pay_to + datetime.timedelta(days=3), template_map)
	change_sched(emp_map[employee], emp_map[employee]['schedules'], emp_map[employee].get('csa'))
	processed_def_sched(employee, pay_from - datetime.timedelta(days=3), pay_to + datetime.timedelta(days=3), emp_map[employee]['schedules'])

	for sched in emp_map[employee]['schedules']:
		shifts = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s LIMIT 1""",(sched['work_shift']), as_dict=True)
		if shifts:
			disable_straight_shift = 1
			period_disable_straight_shift = None
			if period:
				period_disable_straight_shift, approval_cutoff = frappe.db.get_value("Payroll Period", period, ["disable_straight_shift", "approval_cutoff"] )

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
				"is_restday": shifts[0].is_restday,
				"card_in": "",
				"card_out": "",
				"break_in": "",
				"break_out": "",
				"dtrp_links": [],
			}
			
			enable_straight_shift = frappe.db.get_single_value('Timekeeping Settings', 'enable_straight_shift')
			if enable_straight_shift and not period_disable_straight_shift:
				disable_straight_shift = 0

			cards_in, cards_out = get_card_within(entry, sched['target_date'], emp_map[employee]['timelogs_map'], emp_map[employee]['schedules'], 
				shift_map, entry.get('pre_shift'), entry.get('end_preshift'), entry.get('post_shift'), entry.get('end_postshift'), 
				emp_map[employee]['timecards'], emp_map[employee]['dtrp'], emp_map[employee]['tla'], disable_straight_shift)
			sorted_card_list = get_sorted_card(entry, cards_in, cards_out, emp_map[employee]['timelogs_map'])
			if getdate(sched['target_date']) in daterange(pay_from, pay_to):
				result.append(entry)

	return result

def get_shift_map():
	shift_map = {}
	shifts = frappe.db.sql("""SELECT `name`, work_hours, override_hrs, grace_period, b_grace_period, is_restday, is_multi_break, max_break,
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
			"is_multi_break": d.is_multi_break,
			"max_break": d.max_break,
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

	ut_apps = frappe.db.sql("""SELECT `name`, from_time, to_time, from_date, to_date, target_date FROM `tabUndertime Application` 
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

def get_last_current_next_shift(target_date, schedules, timelogs_map, shift_map):
	result = {}
	#Get Last Shift
	last_target_date = target_date - datetime.timedelta(days=1)
	last_shift = filter(lambda empid: getdate(last_target_date) == getdate(empid['target_date']), schedules)
	last_shift_in = None
	last_shift_out = None
	if last_shift:
		last_shift = last_shift[0]['work_shift']
		last_shift_in = get_datetime(str(last_target_date)+" "+str(shift_map[last_shift]['time_in']))
		if shift_map[last_shift]['time_in'] > shift_map[last_shift]['time_out']:
			last_target_date = last_target_date + datetime.timedelta(days=1)
		last_shift_out = get_datetime(str(last_target_date)+" "+str(shift_map[last_shift]['time_out']))

	#Get Next Shift
	next_target_date = target_date + datetime.timedelta(days=1)
	next_shift = filter(lambda empid: next_target_date == empid['target_date'], schedules)
	next_shift_in = None
	next_shift_out = None
	if next_shift:
		next_shift = next_shift[0]['work_shift']
		next_shift_in = get_datetime(str(next_target_date)+" "+str(shift_map[next_shift]['time_in']))
		if shift_map[next_shift]['time_in'] > shift_map[next_shift]['time_out']:
			next_target_date = next_target_date + datetime.timedelta(days=1)
		next_shift_out = get_datetime(str(next_target_date)+" "+str(shift_map[next_shift]['time_out']))
		if shift_map[next_shift]['grace_period']:
			next_shift_in = next_shift_in + datetime.timedelta(minutes=shift_map[next_shift]['grace_period'])

	#Current Shift
	current_shift = filter(lambda empid: target_date == empid['target_date'], schedules)
	current_shift_in = None
	current_shift_out = None
	current_shift_in_ungraced = None
	new_target_date = target_date	
	if current_shift:
		current_shift = current_shift[0]['work_shift']
		current_shift_in = get_datetime(str(target_date)+" "+str(shift_map[current_shift]['time_in']))
		if shift_map[current_shift]['time_in'] > shift_map[current_shift]['time_out']:
			new_target_date = target_date + datetime.timedelta(days=1)
		current_shift_out = get_datetime(str(new_target_date)+" "+str(shift_map[current_shift]['time_out']))
		current_shift_in_ungraced = current_shift_in
		if shift_map[current_shift]['grace_period']:
			current_shift_in = current_shift_in + datetime.timedelta(minutes=shift_map[current_shift]['grace_period'])

	orig_last_target_date = target_date - datetime.timedelta(days=1)
	orig_next_target_date = target_date + datetime.timedelta(days=1)

	last_shift_cardout = None
	if timelogs_map and orig_last_target_date in timelogs_map and timelogs_map[orig_last_target_date] and timelogs_map[orig_last_target_date]['card_out']:
		#if get_datetime(last_shift_out) <= get_datetime(timelogs_map[orig_last_target_date]['card_out']):
		last_shift_cardout = get_datetime(timelogs_map[orig_last_target_date]['card_out'])

	result['last_target_date'] = last_target_date
	result['last_shift'] = last_shift
	result['last_shift_in'] = last_shift_in
	result['last_shift_out'] = last_shift_out
	result['next_target_date'] = next_target_date
	result['next_shift'] = next_shift
	result['next_shift_in'] = next_shift_in
	result['next_shift_out'] = next_shift_out
	result['current_shift'] = current_shift
	result['current_shift_in'] = current_shift_in
	result['current_shift_out'] = current_shift_out
	result['new_target_date'] = new_target_date
	result['orig_last_target_date'] = orig_last_target_date
	result['orig_next_target_date'] = orig_next_target_date
	result['last_shift_cardout'] = last_shift_cardout
	result['current_shift_in_ungraced'] = current_shift_in_ungraced

	return result

def validate_card_log(card_datetime, card_type, lcn_shifts, target_date, card_map, disable_straight_shift, is_dtrp=0):
	to_append = 0
	enable_straight_shift = frappe.db.get_single_value('Timekeeping Settings', 'enable_straight_shift')

	if (card_type in [0, 2, "Time in", "Break out"]):
		to_append = 0
		if enable_straight_shift and not disable_straight_shift:
			range_from = None
			if lcn_shifts['last_shift_out']:
				range_from = lcn_shifts['last_shift_out']

			if lcn_shifts['last_shift_cardout']:
				range_from = lcn_shifts['last_shift_cardout']

			if is_dtrp:
				range_from = card_datetime

			if range_from and range_from <= card_datetime < lcn_shifts['current_shift_out']:
				to_append = 1
				
				if card_datetime >= lcn_shifts['current_shift_in_ungraced']:
					to_append = 1
				else:
					if lcn_shifts['last_shift_cardout']:
						if card_datetime < lcn_shifts['last_shift_cardout']:
							to_append = 0
					else:
						to_append = 1

				if lcn_shifts['last_shift_cardout']:
					if card_datetime >= lcn_shifts['last_shift_cardout']:
						to_append = 1
					
					if target_date in card_map and card_map[target_date]['time_in']:
						min_card_datetime = min(card_map[target_date]['time_in'])
						if card_datetime > min_card_datetime and card_datetime > lcn_shifts['last_shift_cardout'] and not is_dtrp:
							to_append = 0

				if target_date not in card_map:
					card_map[target_date] = {
						'time_in': [],
						'time_out': [],
						'break_out': [],
						'break_in': [],
					}

				if card_type == 0:
					card_map[target_date]['time_in'].append(card_datetime)
		else:
			if lcn_shifts['pre_shift'] and lcn_shifts['max_preshift']:
				if get_datetime(lcn_shifts['pre_shift']) <= get_datetime(card_datetime) <= get_datetime(lcn_shifts['max_preshift']): 
					to_append = 1

	if (card_type in [1, 3, "Time out", "Break in"]):
		to_append = 0
		if enable_straight_shift and not disable_straight_shift:
			if lcn_shifts['next_shift_in'] and lcn_shifts['current_shift_in']:
				if get_datetime(lcn_shifts['current_shift_in']) <= get_datetime(card_datetime) <= get_datetime(lcn_shifts['next_shift_in']): 
					to_append = 1
		else:
			if lcn_shifts['post_shift'] and lcn_shifts['max_postshift']:
				if get_datetime(lcn_shifts['post_shift']) <= get_datetime(card_datetime) <= get_datetime(lcn_shifts['max_postshift']): 
					to_append = 1

	return to_append

def validate_straight_dtrp(target_date, dtrp):
	valid_dtrp = 1
	
	next_date = target_date + datetime.timedelta(days=1)
	target_dtr = list(filter(lambda x: getdate(x['target_date']) == getdate(target_date) and x['card_type'] in [1, '1'], dtrp))
	next_dtr = list(filter(lambda x: getdate(x['target_date']) == getdate(next_date) and x['card_type'] in [0, '0'], dtrp))

	if target_dtr and next_dtr:
		target_dtr = target_dtr[0]
		next_dtr = next_dtr[0]
		approved_dtrs = [target_dtr, next_dtr]
		max_approved_dtr = max(approved_dtrs, key=lambda x:x['approved_on'])
		if max_approved_dtr['name'] == next_dtr['name']:
			valid_dtrp = 0

	return valid_dtrp

def get_card_within(entry, target_date, timelogs_map, schedules, shift_map, pre_shift, max_preshift, post_shift, max_postshift, timecard_list, dtrp=None, tla=None, disable_straight_shift=0):
	cards_in = []
	cards_out = []
	dtrp_override = frappe.db.get_single_value('Timekeeping Settings', 'dtrp_override')
	lcn_shifts = get_last_current_next_shift(target_date, schedules, timelogs_map, shift_map)
	lcn_shifts['pre_shift'] = pre_shift
	lcn_shifts['max_preshift'] = max_preshift
	lcn_shifts['post_shift'] = post_shift
	lcn_shifts['max_postshift'] = max_postshift

	card_map = {}
	for tc in sorted(timecard_list, key=lambda k: k['card_datetime'], reverse=1):
		if (tc.card_type == 0 or tc.card_type == 2):
			if validate_card_log(tc.card_datetime, tc.card_type, lcn_shifts, target_date, card_map, disable_straight_shift):
				cards_in.append({
					"card_name":tc.name,
					"card_time":tc.time,
					"card_datetime": tc.card_datetime,
					"card_type": tc.card_type,
					"from": 'Timecard',
				})

		if (tc.card_type == 1 or tc.card_type == 3):
			if validate_card_log(tc.card_datetime, tc.card_type, lcn_shifts, target_date, card_map, disable_straight_shift):
				cards_out.append({
					"card_name":tc.name,
					"card_time":tc.time,
					"card_datetime": tc.card_datetime,
					"card_type": tc.card_type,
					"from": 'Timecard',
				})

	if tla:
		no_card_in, no_card_out, no_break_out, no_break_in = 1, 1, 1, 1
		for tl in tla:
			time_req = get_datetime(str(getdate(tl['target_date']))+" "+str(tl['request']))
			if tl['type'] == 'Time In':
				card_type = 0
			if tl['type'] == 'Time Out':
				card_type = 1
			if tl['type'] == 'Break In':
				card_type = 3
			if tl['type'] == 'Break Out':
				card_type = 2

			for c_in in cards_in:
				if card_type == c_in['card_type']:
					if validate_card_log(time_req, card_type, lcn_shifts, target_date, card_map, disable_straight_shift):
						if c_in['from'] == 'Timecard':
							c_in['card_name'] = tl['name']
							c_in['card_date'] = tl['target_date']
							c_in['card_time'] = tl['request']
							c_in['card_datetime'] = time_req
							c_in['card_type'] = card_type

						if card_type == 0:
							no_card_in = 0
						if card_type == 2:
							no_break_out = 0

			for c_out in cards_out:
				if card_type == c_out['card_type']:
					if validate_card_log(time_req, card_type, lcn_shifts, target_date, card_map, disable_straight_shift):
						if c_out['from'] == 'Timecard':
							c_out['card_name'] = tl['name']
							c_out['card_date'] = tl['target_date']
							c_out['card_time'] = tl['request']
							c_out['card_datetime'] = time_req
							c_out['card_type'] = card_type

						if card_type == 1:
							no_card_out = 0
						if card_type == 3:
							no_break_in = 0

			if no_card_in == 1 or no_break_out == 1:
				if tl['type'] in ['Time In', 'Break Out']:
					if validate_card_log(time_req, card_type, lcn_shifts, target_date, card_map, disable_straight_shift):
						cards_in.append({
							"card_name": tl['name'],
							"card_time": tl['request'],
							"card_datetime": time_req,
							"card_type": card_type,
							"from": 'Timelogs Application',
						})

			if no_card_out == 1 or no_break_in == 1:
				if tl['type'] in ['Time Out', 'Break In']:
					if validate_card_log(time_req, card_type, lcn_shifts, target_date, card_map, disable_straight_shift):
						cards_out.append({
							"card_name": tl['name'],
							"card_time": tl['request'],
							"card_datetime": time_req,
							"card_type": card_type,
							"from": 'Timelogs Application',
						})

	no_card_in, no_card_out, no_break_out, no_break_in = 1, 1, 1, 1
	dtro_time_in, dtro_break_out, dtro_break_in, dtro_time_out = [], [], [], []

	for dt in dtrp:
		if not dtrp_override:
			if getdate(target_date) == getdate(dt['target_date']):
				for c_in in cards_in:
					if dt['card_type'] == c_in['card_type']:
						is_valid_dtrp = 1
						if lcn_shifts['last_shift_cardout']:
							if get_datetime(dt['card_datetime']) < get_datetime(lcn_shifts['last_shift_cardout']):
								is_valid_dtrp = 0

						#if not validate_straight_dtrp(target_date, dtrp):
						#	is_valid_dtrp = 0

						if is_valid_dtrp and validate_card_log(dt['card_datetime'], dt['card_type'], lcn_shifts, target_date, card_map, disable_straight_shift, is_dtrp=1):
							if c_in['from'] == 'Timecard':
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
					if dt['card_type'] == c_out['card_type']:
						is_valid_dtrp = 1
						#if not validate_straight_dtrp(target_date, dtrp):
						#	is_valid_dtrp = 0

						if is_valid_dtrp and validate_card_log(dt['card_datetime'], dt['card_type'], lcn_shifts, target_date, card_map, disable_straight_shift, is_dtrp=1):
							if c_out['from'] == 'Timecard':
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
					if (dt['card_type'] == 0 or dt['card_type'] == 2):
						is_valid_dtrp = 1
						if lcn_shifts['last_shift_cardout']:
							if get_datetime(dt['card_datetime']) < get_datetime(lcn_shifts['last_shift_cardout']):
								is_valid_dtrp = 0

						if is_valid_dtrp and validate_card_log(dt['card_datetime'], dt['card_type'], lcn_shifts, target_date, card_map, disable_straight_shift, is_dtrp=1):
							cards_in.append({
								"card_name": dt['name'],
								"card_date": dt['target_date'],
								"card_time": dt['request'],
								"card_datetime": dt['card_datetime'],
								"card_type": dt['card_type'],
								"from": 'DTRP Application',
							})

							entry['is_dtrp'] = 1
							if dt['name'] not in entry['dtrp_links']:
								entry['dtrp_links'].append(dt['name'])

				if no_card_out == 1 or no_break_in == 1:
					if (dt['card_type'] == 1 or dt['card_type'] == 3):
						is_valid_dtrp = 1
						#if not validate_straight_dtrp(target_date, dtrp):
						#	is_valid_dtrp = 0

						if is_valid_dtrp and validate_card_log(dt['card_datetime'], dt['card_type'], lcn_shifts, target_date, card_map, disable_straight_shift, is_dtrp=1):
							cards_out.append({
								"card_name": dt['name'],
								"card_date": dt['target_date'],
								"card_time": dt['request'],
								"card_datetime": dt['card_datetime'],
								"card_type": dt['card_type'],
								"from": 'DTRP Application',
							})

							entry['is_dtrp'] = 1
							if dt['name'] not in entry['dtrp_links']:
								entry['dtrp_links'].append(dt['name'])

		if dtrp_override:
			if getdate(dt['target_date']) == getdate(target_date):
				if dt['card_type'] == 0:
					dtro_time_in = [{
						"card_name": dt['name'],
						"card_date": dt['target_date'],
						"card_time": dt['request'],
						"card_datetime": dt['card_datetime'],
						"card_type": dt['card_type']
					}]

				if dt['card_type'] == 2:
					dtro_break_out = [{
						"card_name": dt['name'],
						"card_date": dt['target_date'],
						"card_time": dt['request'],
						"card_datetime": dt['card_datetime'],
						"card_type": dt['card_type']
					}]

				if dt['card_type'] == 3:
					dtro_break_in = [{
						"card_name": dt['name'],
						"card_date": dt['target_date'],
						"card_time": dt['request'],
						"card_datetime": dt['card_datetime'],
						"card_type": dt['card_type']
					}]

				if dt['card_type'] == 1:
					dtro_time_out = [{
						"card_name": dt['name'],
						"card_date": dt['target_date'],
						"card_time": dt['request'],
						"card_datetime": dt['card_datetime'],
						"card_type": dt['card_type']
					}]

	if dtro_time_in or dtro_break_out:
		cards_in = []

	if dtro_break_in or dtro_time_out:
		cards_out = []

	if dtro_time_in:
		cards_in.extend(dtro_time_in)

	if dtro_break_out:
		cards_in.extend(dtro_break_out)

	if dtro_break_in:
		cards_out.extend(dtro_break_in)

	if dtro_time_out:
		cards_out.extend(dtro_time_out)

	return cards_in, cards_out

def get_sorted_card(entry, cards_in, cards_out, timelogs_map):
	sorted_in = sorted(cards_in, key=lambda k: k['card_datetime'])
	sorted_out = sorted(cards_out, key=lambda k: k['card_datetime'])
	card_in = None
	break_out = None
	card_out = None
	break_in = None

	for card in sorted_in:
		if card['card_type'] == 0:
			if entry['card_in'] == "":
				entry['card_in'] = card['card_datetime']
				card_in = card['card_datetime']
		elif card['card_type'] == 2:
			if entry['break_out'] == "":
				entry['break_out'] = card['card_datetime']
				break_out = card['card_datetime']
 	
 	for card in sorted_out:
		if card['card_type'] == 1:
			if entry['card_in']:
				if entry['card_in'] <= card['card_datetime']:
					entry['card_out'] = card['card_datetime']
					card_out = card['card_datetime']
			else:
				entry['card_out'] = card['card_datetime']
				card_out = card['card_datetime']

		elif card['card_type'] == 3:
			if entry['break_out']:
				if entry['break_out'] <= card['card_datetime']:
					entry['break_in'] = card['card_datetime']
					break_in = card['card_datetime']
			else:
				entry['break_in'] = card['card_datetime']
				break_in = card['card_datetime']

	if entry['target_date'] not in timelogs_map:
		timelogs_map[entry['target_date']] = {
			'card_in': card_in,
			'break_out': break_out,
			'card_out': card_out,
			'break_in': break_in,
		}

 	return entry

def get_multi_breaks(entry, cards_in, cards_out):
	break_outs = []
	break_ins = []
	break_pairs = []

	sorted_in = sorted(cards_in, key=lambda k: k['card_datetime'])
	sorted_out = sorted(cards_out, key=lambda k: k['card_datetime'])
	time_in = get_datetime(str(getdate(entry['target_date']))+" "+str(entry['time_in']))
	time_out = get_datetime(str(getdate(entry['target_date']))+" "+str(entry['time_out']))

	for card in sorted_in:
		if card['card_type'] == 2:
			if card['card_datetime'] < time_in:
				card['card_datetime'] = time_in
			break_outs.append(card['card_datetime'])
 	
 	for card in sorted_out:
		if card['card_type'] == 3:
			if card['card_datetime'] > time_out:
				card['card_datetime'] = time_out
			break_ins.append(card['card_datetime'])

	if break_ins and break_outs:
		while break_outs:
			is_valid = 1
			remove_endpair = 0
			remove_startpair = 0
			start_pair = None
			end_pair = None

			if break_outs:
				start_pair = min(break_outs)
			if break_ins:
				end_pair = min(break_ins)

			if not (time_in <= start_pair <= time_out):
				remove_startpair = 1
			if not (time_in <= end_pair <= time_out):
				remove_endpair = 1
			if entry['card_in'] and entry['card_out']:
				if not (entry['card_in'] <= start_pair <= entry['card_out']):
					remove_endpair = 1
				if not (entry['card_in'] <= end_pair <= entry['card_out']):
					remove_endpair = 1

			if start_pair and end_pair and not remove_startpair and not remove_endpair:
				if end_pair < start_pair:
					remove_endpair = 1
					is_valid = 0

				for bpair in break_pairs:
					if get_datetime(bpair['break_out']) < get_datetime(end_pair) < get_datetime(bpair['break_in']):
						remove_endpair = 1
						is_valid = 0

					if get_datetime(bpair['break_out']) < get_datetime(start_pair) < get_datetime(bpair['break_in']):
						remove_startpair = 1
						is_valid = 0

				if is_valid:
					break_pairs.append({
						'break_out': start_pair,
						'break_in': end_pair,
						'break_mins': (end_pair - start_pair).total_seconds() / 60
					})
					remove_endpair = 1
					remove_startpair = 1

			if remove_endpair:
				break_ins.remove(end_pair)
			if remove_startpair:
				break_outs.remove(start_pair)

			if not break_ins:
				break_outs = []

	entry['break_pairs'] = []
	entry['break_pairs'] = break_pairs

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
	entry['tla_links'] = None

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
		"cost_center": emp.cost_center,
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
		"is_multi_break": shift_map[sched['work_shift']]['is_multi_break'],
		"max_break": shift_map[sched['work_shift']]['max_break'],
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
		"ot_early_nd": 0.0,
		"ot_late_nd": 0.0,
		"overtime_ex": 0.0,
		"overtime_ndex": 0.0,
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
		#ND Rate Class
		"earlynightdiff": 0,
		"latenightdiff": 0,
		#LINKs
		"lv_links": [],
		"ot_links": [],
		"ob_links": [],
		"ext_links": [],
		"ut_links": [],
		"cto_links": [],
		"dtrp_links": [],
		"tla_links": [],
		#SHIFT POLICIES
		"graceperiod_late": shift_map[sched['work_shift']]['graceperiod_late'],
		"straight_ot": shift_map[sched['work_shift']]['straight_ot'],
		"allow_ot_in_shift": shift_map[sched['work_shift']]['allow_ot_in_shift'],
		"flexible_type": shift_map[sched['work_shift']]['flexible_type'],
		#GLOBAL POLICIES
		"ot_deduct_late": flt(frappe.db.get_single_value('Timekeeping Settings', 'ot_deduct_late'), 8),
		"ot_deduct_ut": flt(frappe.db.get_single_value('Timekeeping Settings', 'ot_deduct_ut'), 8),
		"ot_start_delay": flt(frappe.db.get_single_value('Timekeeping Settings', 'ot_start_delay'), 8),
		"ot_interval": flt(frappe.db.get_single_value('Timekeeping Settings', 'ot_interval'), 8),
		"max_holiday_ot": flt(frappe.db.get_single_value('Timekeeping Settings', 'max_holiday_ot'), 8),
		"late_interval": flt(frappe.db.get_single_value('Timekeeping Settings', 'late_interval'), 8),
		"ut_interval": flt(frappe.db.get_single_value('Timekeeping Settings', 'ut_interval'), 8),
		"ot_strict_logs": flt(frappe.db.get_single_value('Timekeeping Settings', 'ot_strict_logs'), 8),
		"hd_halfcard": flt(frappe.db.get_single_value('Timekeeping Settings', 'hd_halfcard'), 8),
		"ot_dedlt_ho": frappe.db.get_single_value('Timekeeping Settings', 'ot_dedlt_ho'),
		"ot_dedut_ho": frappe.db.get_single_value('Timekeeping Settings', 'ot_dedut_ho'),
		"dn_ot_late": frappe.db.get_single_value('Timekeeping Settings', 'dn_ot_late'),
		"dn_ot_ut": frappe.db.get_single_value('Timekeeping Settings', 'dn_ot_ut'),
		"at_work_rdho": frappe.db.get_single_value('Timekeeping Settings', 'at_work_rdho'),
		"mo_abho": frappe.db.get_single_value('Timekeeping Settings', 'mo_abho'),
		"ab_regho": frappe.db.get_single_value('Timekeeping Settings', 'ab_regho'),
		"ext_deduct": frappe.db.get_single_value('Timekeeping Settings', 'ext_deduct'),
		"lt_int_rup": frappe.db.get_single_value('Timekeeping Settings', 'lt_int_rup'),
	}
	
	return entry

def init_employee_map(employees, employee, company, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs = None):
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
				"tla": [],
				"timelogs_map": {},
			})
		)

	get_all_overrides(emp_map, employee, pay_from, pay_to)
	get_all_schedules(emp_map, employee, pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1))
	get_all_timecards(emp_map, employee, pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1)) #+1 date to get nextday logs
	get_all_holidays(emp_map, pay_from, pay_to)
	#applications
	get_all_leaves(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment,monthly_approval_cutoffs)
	get_all_ots(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs)
	get_all_obs(emp_map, employee, pay_from - datetime.timedelta(days=1), pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs)
	get_all_uts(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs)
	get_all_ext(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs)
	get_all_cto(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs)
	get_all_wss(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment)
	get_all_csa(emp_map, employee, pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1), approval_cutoff, adjustment, monthly_approval_cutoffs)
	get_all_dtrp(emp_map, employee, pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1), approval_cutoff, adjustment, monthly_approval_cutoffs)
	get_all_tla(emp_map, employee, pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1), approval_cutoff, adjustment)

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

def get_all_leaves(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs = None):
	conditions_list = []
	if adjustment != 1 and not monthly_approval_cutoffs:
		conditions_list.append("L.approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("L.employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""


	if monthly_approval_cutoffs and not adjustment:
		leaves = frappe.db.sql("""SELECT L.`name`, L.employee, L.leave_type, LA.leave_date, 
			LA.is_half_day, LA.is_second_half, LA.is_holiday, LA.is_excluded, L.is_lwop
			FROM `tabLeave Application Table` LA
			INNER JOIN `tabLeave Application` L ON L.`name` = LA.parent INNER JOIN `tabPayroll Period` PP ON L.`company` = PP.`company`
			WHERE LA.leave_date >= %s AND LA.leave_date <= %s {conditions} 
			AND L.docstatus = '1' AND L.workflow_state = 'Approved' AND L.convert_cash != 1
			AND L.approved_on <= PP.approval_cutoff AND LA.`leave_date` BETWEEN PP.`attendance_from` and PP.`attendance_to`
			ORDER BY LA.leave_date ASC """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	else:
		leaves = frappe.db.sql("""SELECT L.`name`, L.employee, L.leave_type, LA.leave_date, 
			LA.is_half_day, LA.is_second_half, LA.is_holiday, LA.is_excluded, L.is_lwop
			FROM `tabLeave Application Table` LA
			INNER JOIN `tabLeave Application` L ON L.`name` = LA.parent
			WHERE LA.leave_date >= %s AND LA.leave_date <= %s {conditions} 
			AND L.docstatus = '1' AND L.workflow_state = 'Approved' AND L.convert_cash != 1
			ORDER BY LA.leave_date ASC """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	for d in leaves:
		if d.employee in emp_map:
			emp_map[d.employee].lvs.append(d)

def get_all_obs(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs = None):
	conditions_list = []
	if adjustment != 1 and not monthly_approval_cutoffs:
		conditions_list.append("approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("OBA.employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""
	if monthly_approval_cutoffs and not adjustment:
		ob_apps = frappe.db.sql("""SELECT OBA.`name`, OBA.employee, OBAT.target_date, OBAT.date, OBAT.to_date,OBAT.from_time, OBAT.to_time, OBAT.hrs, OBAT.is_holiday, OBAT.is_excluded 
			FROM `tabOfficial Business Application Table` OBAT
			INNER JOIN `tabOfficial Business Application` OBA  ON OBAT.parent = OBA.`name` INNER JOIN `tabPayroll Period` PP ON OBA.`company` = PP.`company`
			WHERE OBA.workflow_state = 'Approved' AND OBAT.target_date >= %s 
			AND OBAT.target_date <= %s AND OBAT.is_excluded = 0 AND OBA.approved_on <= PP.approval_cutoff 
			AND OBAT.`target_date` BETWEEN PP.`attendance_from` and PP.`attendance_to` {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	else:
		ob_apps = frappe.db.sql("""SELECT OBA.`name`, OBA.employee, OBAT.target_date, OBAT.date, OBAT.to_date,OBAT.from_time, OBAT.to_time, OBAT.hrs, OBAT.is_holiday, OBAT.is_excluded 
			FROM `tabOfficial Business Application Table` OBAT
			INNER JOIN `tabOfficial Business Application` OBA  ON OBAT.parent = OBA.`name`
			WHERE OBA.workflow_state = 'Approved' AND OBAT.target_date >= %s 
			AND OBAT.target_date <= %s 
			AND OBAT.is_excluded = 0 {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)
	
	for d in ob_apps:
		if d.employee in emp_map:
			emp_map[d.employee].obs.append(d)

def get_all_ots(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs = None):
	conditions_list = []
	if adjustment != 1 and not monthly_approval_cutoffs:
		conditions_list.append("approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	if monthly_approval_cutoffs and not adjustment:
		overtimes = frappe.db.sql("""SELECT OA.`name`, OA.employee, OA.total_hrs, OA.break_hrs, OA.target_date, OA.from_date, OA.to_date, OA.from_time, OA.to_time FROM `tabOvertime Application` OA
			INNER JOIN `tabPayroll Period` PP ON OA.`company` = PP.`company`
			WHERE OA.workflow_state = 'Approved' AND OA.target_date >= %s AND OA.approved_on <= PP.approval_cutoff AND OA.`target_date` BETWEEN PP.`attendance_from` and PP.`attendance_to`
			AND OA.target_date <= %s {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	else:
		overtimes = frappe.db.sql("""SELECT `name`, employee, total_hrs, break_hrs, target_date, from_date, to_date, from_time, to_time FROM `tabOvertime Application` 
			WHERE workflow_state = 'Approved' AND target_date >= %s 
			AND target_date <= %s {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	for d in overtimes:
		if d.employee in emp_map:
			emp_map[d.employee].ots.append(d)

def get_all_uts(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs = None):
	conditions_list = []
	if adjustment != 1 and not monthly_approval_cutoffs:
		conditions_list.append("approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""
	if monthly_approval_cutoffs and not adjustment:
		undertimes = frappe.db.sql("""SELECT UA.`name`, UA.employee, UA.from_time, UA.to_time, UA.from_date, UA.to_date, UA.target_date FROM `tabUndertime Application` UA
			INNER JOIN `tabPayroll Period` PP ON UA.`company` = PP.`company`
			WHERE UA.workflow_state = 'Approved' AND UA.from_date >= %s AND UA.from_date <= %s 
			AND UA.approved_on <= PP.approval_cutoff AND UA.`target_date` BETWEEN PP.`attendance_from` and PP.`attendance_to` 
			{conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	else:
		undertimes = frappe.db.sql("""SELECT `name`, employee, from_time, to_time, from_date, to_date, target_date FROM `tabUndertime Application` 
			WHERE workflow_state = 'Approved' AND from_date >= %s 
			AND from_date <= %s {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	for d in undertimes:
		if d.employee in emp_map:
			emp_map[d.employee].uts.append(d)

def get_all_cto(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs = None):
	conditions_list = []
	if adjustment != 1 and not monthly_approval_cutoffs:
		conditions_list.append("approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")
		
	if employee:
		conditions_list.append("employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	if monthly_approval_cutoffs and not adjustment:
		compensatory = frappe.db.sql("""SELECT CTO.`name`, CTO.employee, CTT.cto_hours as use_total_hours, CTT.target_date as use_target_date, 
			CTT.from_date as use_from_date, CTT.to_date as use_to_date, CTT.from_time as use_fromtime, CTT.to_time as use_totime, CTT.break_hours
			FROM `tabCompensatory Time Off` CTO 
			INNER JOIN `tabCompensatory Time Off Targets` CTT ON CTO.`name` = CTT.`parent`
			INNER JOIN `tabPayroll Period` PP ON CTO.`company` = PP.`company`
			WHERE CTO.workflow_state = 'Approved' AND CTT.target_date >= %s AND CTT.target_date <= %s
			AND CTO.`type` = 'Use' AND CTO.approved_on <= PP.approval_cutoff 
			AND CTT.`target_date` BETWEEN PP.`attendance_from` and PP.`attendance_to`{conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)
	else:
		compensatory = frappe.db.sql("""SELECT CTO.`name`, CTO.employee, CTT.cto_hours as use_total_hours, CTT.target_date as use_target_date, 
			CTT.from_date as use_from_date, CTT.to_date as use_to_date, CTT.from_time as use_fromtime, CTT.to_time as use_totime, CTT.break_hours
			FROM `tabCompensatory Time Off` CTO INNER JOIN `tabCompensatory Time Off Targets` CTT ON CTO.`name` = CTT.`parent`
			WHERE CTO.workflow_state = 'Approved' AND CTT.target_date >= %s AND CTT.target_date <= %s
			AND CTO.`type` = 'Use' {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)
	
	for d in compensatory:
		if d.employee in emp_map:
			emp_map[d.employee].cto.append(d)

def get_all_ext(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs = None):
	conditions_list = []
	if adjustment != 1 and not monthly_approval_cutoffs:
		conditions_list.append("approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	if monthly_approval_cutoffs and not adjustment:
		ex_tardiness = frappe.db.sql("""SELECT ETA.`name`, ETA.employee, ETA.`date`, ETA.from_time, ETA.to_time, ETA.`type` 
			FROM `tabExcuse Tardiness Application` ETA INNER JOIN `tabPayroll Period` PP ON ETA.`company` = PP.`company`
			WHERE ETA.workflow_state = 'Approved' AND ETA.`date` >= %s AND ETA.`date` <= %s AND ETA.approved_on <= PP.approval_cutoff 
			AND ETA.`date` BETWEEN PP.`attendance_from` and PP.`attendance_to`{conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)
	else:
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
		WHERE WS.docstatus = 1 AND suspension_start != suspension_end AND suspension_date >= %s
        AND suspension_date <= %s {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	for d in ws_apps:
		if d.employee in emp_map:
			emp_map[d.employee].wss.append(d)

def get_all_csa(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs = None):
	conditions_list = []
	multi_csa = {}
	
	if employee:
		conditions_list.append("CSA.employee='"+cstr(employee)+"' ")

	if adjustment != 1 and not monthly_approval_cutoffs:
		conditions_list.append("DATE(CSA.approved_on) <= '"+ cstr(getdate(approval_cutoff)) +"'")


	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""
	if monthly_approval_cutoffs and not adjustment:
		cs_apps = frappe.db.sql(""" SELECT CSA.employee, CSA.approved_on, CSAT.target_date, CSAT.new_shift
			FROM `tabChange Schedule Application` CSA INNER JOIN `tabPayroll Period` PP ON CSA.`company` = PP.`company`
			INNER JOIN `tabChange Schedule Application Table` CSAT ON CSAT.parent = CSA.`name` 
			WHERE CSA.docstatus = 1 AND CSA.`workflow_state` = 'Approved' AND CSAT.target_date >= %(pay_from)s AND CSAT.target_date <= %(pay_to)s AND CONVERT(CSA.approved_on, DATE) <= PP.approval_cutoff 
			AND CSAT.`target_date` BETWEEN PP.`attendance_from` and PP.`attendance_to`
			{conditions} ORDER BY CSA.modified ASC """.format( conditions=conditions ), {'pay_from': pay_from, 'pay_to': pay_to}, as_dict=1)
		
	else:
		cs_apps = frappe.db.sql(""" SELECT CSA.employee, CSA.approved_on, CSAT.target_date, CSAT.new_shift
			FROM `tabChange Schedule Application` CSA 
			INNER JOIN `tabChange Schedule Application Table` CSAT ON CSAT.parent = CSA.`name` 
			WHERE CSA.docstatus = 1 AND CSA.`workflow_state` = 'Approved' AND CSAT.target_date >= %s AND CSAT.target_date <= %s 
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

def get_all_dtrp(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment, monthly_approval_cutoffs = None):
	conditions_list = []
	multi_dtrp = {}
	if adjustment != 1 and not monthly_approval_cutoffs:
		conditions_list.append("CONVERT(DA.`approved_on`, DATE) <= '"+ cstr(getdate(approval_cutoff)) +"'")
	#if adjustment == 1:
	#	conditions_list.append("DA.approved_on >= '"+ cstr(getdate(approval_cutoff)) +"' ")
	#else:
	#	conditions_list.append("DA.approved_on <= '"+ cstr(getdate(approval_cutoff)) +"' ")

	if employee:
		conditions_list.append("DA.employee='"+ cstr(employee) +"'")

	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""
	if monthly_approval_cutoffs and not adjustment:
		dtr_apps = frappe.db.sql(""" SELECT DA.`name`, DA.`employee`, TIMESTAMP(DA.`dtr_date`, DT.`request`) as card_datetime, 
			DA.`target_date`, DT.`request`, DT.`type`, DA.`approved_on`, DT.`card_type`, DA.`is_previous`
			FROM `tabDTR Problem Table` DT INNER JOIN `tabDTR Problem Application` DA ON DT.`parent`=DA.`name` INNER JOIN `tabPayroll Period` PP ON DA.`company` = PP.`company`
			WHERE DA.`workflow_state` = 'Approved'
			AND DA.`target_date` >= %s AND DA.`target_date` <= %s 
			AND CONVERT(DA.`approved_on`, DATE) <= PP.`approval_cutoff` AND DA.`target_date` BETWEEN PP.`attendance_from` and PP.`attendance_to` {conditions}
			ORDER BY card_datetime """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)
	else:
		dtr_apps = frappe.db.sql(""" SELECT DA.`name`, DA.`employee`, TIMESTAMP(DA.`dtr_date`, DT.`request`) as card_datetime, 
			DA.`target_date`, DT.`request`, DT.`type`, DA.`approved_on`, DT.`card_type`, DA.`is_previous`
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

def get_all_tla(emp_map, employee, pay_from, pay_to, approval_cutoff, adjustment):
	conditions_list = []
	multi_tla = {}
	if employee:
		conditions_list.append("TA.employee='"+ cstr(employee) +"'")
	conditions = "and {}".format(" and ".join(conditions_list)) if conditions_list else ""

	tla_apps = frappe.db.sql("""SELECT TA.employee, TAT.location, TAT.cost_center, TA.`approved_on`, TA.`name`,
		TAT.target_date, TAT.type, TAT.request FROM `tabTimelogs Application` TA
		INNER JOIN `tabTimelogs Application Table` TAT ON TA.`name` = TAT.parent 
		WHERE TAT.target_date >= %s AND TAT.target_date <= %s AND TA.docstatus = 1 
		AND TA.workflow_state = 'Approved' {conditions} """.format( conditions=conditions ), (pay_from, pay_to), as_dict=1)

	for d in tla_apps:
		if d.employee in emp_map:
			if d.employee not in multi_tla:
				multi_tla[d.employee] = {}

			if d.target_date not in multi_tla[d.employee]:
				multi_tla[d.employee][d.target_date] = {}

			if d.type not in multi_tla[d.employee][d.target_date]:
				multi_tla[d.employee][d.target_date][d.type] = []

			multi_tla[d.employee][d.target_date][d.type].append(d)

	for m in multi_tla:
		for ml in multi_tla[m]:
			for mlt in multi_tla[m][ml]:
				xml = max(multi_tla[m][ml][mlt], key=lambda x:x['approved_on'])
				emp_map[m].tla.append(xml)

	return tla_apps

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
			if (ar.employee == employee) and (ar.is_default_schedule) and not d['is_change_schedule']:
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
