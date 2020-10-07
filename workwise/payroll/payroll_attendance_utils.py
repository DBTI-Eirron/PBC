from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, cstr, add_to_date

def get_absent_days(at, opt):
	AT = 0.0
	#check monthy rate settings 'opt' for options or setttings
	mo_abho = opt.get('mo_abho') #Monthly Rate Absent on Special Holiday
	ab_regho = opt.get('ab_regho') #Absent on Regular Holiday
	ws_pho = opt.get('ws_pho')

	#if absent or is leave without pay
	if ( at['is_absent'] == 1 or at['is_lwop'] == 1 or at['is_halfday'] == 1):
		if at['is_holiday'] and mo_abho: #if holiday and allowed absent on holiday
			if at['is_sp_holiday']: #special holiday is allowed by default
				AT = 1
			elif (not at['is_sp_holiday']) and ab_regho: #if absent in regular holiday is allowed
				AT = 1
		else:
			if at['is_lwop'] == 1 and at['lv_status'] > 1: #if lwop is 1st half or 2nd half
				AT = 0.5 
				if at.is_absent:
					AT = 1
									
			else: 
				#if absent only no lwop, set to whole day
				#but if with halfday tag set it to halfday 0.5
				AT = 0.5 if at['is_halfday'] == 1 else 1
				if ws_pho:
					if at['lv_status'] == 2 and "2ndhalf Work Suspension" in at['tags']:
						AT = 0
					if at['lv_status'] == 3 and "1sthalf Work Suspension" in at['tags']:
						AT = 0

	return AT

def absent_backup(at, opt):
	#if absent
	if ( at.is_absent == 1 or at.is_lwop == 1 ):
		if not at.is_holiday:
			if at.is_lwop == 1 and at.lv_status > 1:
				absent += ( at.work_hours / 2 ) * flt(rates.get('hourly_rate'), 8)
				absent_days += 0.5
				AT_days += 0.5
				if at.is_halfday: #if lwop halfday with absent halfday add additional 0.5
					absent += ( at.work_hours / 2 ) * flt(rates.get('hourly_rate'), 8)
					absent_days += 0.5
					AT_days += 0.5										
				
				test.append(_(""+cstr(at.target_date)+" "+cstr(absent_days)+""))
			else:
				absent += ( at.work_hours / 2 ) * flt(rates.get('hourly_rate'), 8) if at.is_halfday == 1 else ( at.work_hours ) * flt(rates.get('hourly_rate'), 8)
				absent_days += 0.5 if at.is_halfday == 1 else 1
				AT_days += 0.5 if at.is_halfday == 1 else 1
				test.append(_(""+cstr(at.target_date)+" "+cstr(absent_days)+""))
		
		elif at.is_holiday and header.get('mo_abho'):
			if at.is_lwop == 1 and at.lv_status > 1:
				absent += ( at.work_hours / 2 ) * flt(rates.get('hourly_rate'), 8)
				absent_days += 0.5
				AT_days += 0.5
				if at.is_halfday: #if lwop halfday with absent halfday add additional 0.5
					absent += ( at.work_hours / 2 ) * flt(rates.get('hourly_rate'), 8)
					absent_days += 0.5
					AT_days += 0.5

				test.append(_(""+cstr(at.target_date)+" "+cstr(absent_days)+""))
			else:
				absent += ( at.work_hours / 2 ) * flt(rates.get('hourly_rate'), 8) if at.is_halfday == 1 else ( at.work_hours ) * flt(rates.get('hourly_rate'), 8)
				absent_days += 0.5 if at.is_halfday == 1 else 1
				AT_days += 0.5 if at.is_halfday == 1 else 1
				test.append(_(""+cstr(at.target_date)+" "+cstr(absent_days)+""))
