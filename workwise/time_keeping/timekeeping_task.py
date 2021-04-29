from __future__ import unicode_literals
import frappe, datetime, math, calendar
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from frappe.utils import cint, cstr, flt, nowdate, add_days, getdate, fmt_money, get_datetime, add_to_date
from frappe import _

def get_scheduler():
	pass

def addYears(d, years):
    try:    
        return d.replace(year = d.year + years)
    except ValueError:
        return d + (date(d.year + years, 1, 1) - date(d.year, 1, 1))

def addMonths(d, months):
	return d + relativedelta(months=+months)

def check_condition(condition, diff, value):
	result = 0
	if condition == "equal to":
		if diff == value:
			result = 1
	if condition == "less than":
		if diff < value:
			result = 1
	if condition == "greater than":
		if diff > value:
			result = 1
	if condition == "less than and equal to":
		if diff <= value:
			result = 1
	if condition == "greater than and equal to":
		if diff >= value:
			result = 1
	
	return result

def get_yeardiff(datesource1, datesource2):
	if datesource1 <= datesource2:
		year_diff = abs(datesource2.year - datesource1.year)
		year_diff_res = addYears(datesource1, year_diff)
	else:
		year_diff = abs(datesource1.year - datesource2.year)
		year_diff_res = addYears(datesource2, year_diff)

	year_diff_date = datetime.datetime.strptime(str(getdate(year_diff_res)), '%Y-%m-%d')

	return year_diff, year_diff_res, year_diff_date

def get_monthdiff(datesource1, datesource2):
	month_diff = (datesource1.year - datesource2.year) * 12 + (datesource1.month - datesource2.month)
	month_diff_res = addMonths(datesource2, month_diff)
	month_diff_date = datetime.datetime.strptime(str(datesource1.year)+"-"+str(month_diff_res.month)+"-"+str(month_diff_res.day), '%Y-%m-%d')

	return month_diff, month_diff_res, month_diff_date

def check_rundate(method, datesource):
	result = 0
	if method == "Every Month":
		if datesource.day in [1, 01]:
			result = 1

	if method == "Every Year":
		if (datesource.day in [1, 01]) and (datesource.month in [1, 01]):
			result = 1

	return result

def automated_leave_balance(is_forced=0):
	lb_entries_created = 0
	created_lb_entries = 0
	now_date = nowdate()
	now_date = datetime.datetime.strptime(cstr(getdate(now_date)), '%Y-%m-%d')
	year_end = getdate(datetime.date(datetime.date.today().year, 12, 31))

	#Check for Carry Over Leave Balance
	carry_overs = get_carryover_lvbal()
	for co in carry_overs:
		if validate_create_lbentry({'employee': co['employee'], 'leave_type': co['leave_type']}):
			crow = {
				"employee": co['employee'],
				"company": co['company'],
				"posting_date": co['posting_date'],
				"leave_type": co['leave_type'],
				"balance_type": co['balance_type'],
				"created_from": co['created_from'],
				"from_date": co['from_date'],
				"to_date": co['to_date'],
				"credits": co['credits'],
			}
			if is_forced:
				crow['created_from'] = 'LB Scheduler - Carry Over'
			if validate_duplicate_lbentry(crow, is_forced):
				crow['employee_name'] = co['employee_name']
				crow['deduct_credits_to'] = None
				clb = frappe.new_doc("LB Entry")
				clb.update(crow)
				clb.flags.ignore_permissions = True
				clb.flags.ignore_validate = True
				if clb.insert():
					lb_entries_created = 1
					if is_forced:
						created_lb_entries += 1

	#Check for Leave Balance Setup
	included_employees = []
	setup_included = []
	employee_setup = {}
	setups = []

	#Get employees with leave balance setup
	employee_setup = {}
	employees = frappe.db.sql(""" SELECT `name`, `full_name`, `company`, `leave_balance_setup`, `date_hired` FROM `tabEmployee` WHERE `is_active` = 1 AND `leave_balance_setup` IS NOT NULL """, as_dict=1)
	for emp in employees:
		if emp.leave_balance_setup not in employee_setup:
			employee_setup[emp.leave_balance_setup] = []
			setup_included.append("'"+cstr(emp.leave_balance_setup)+"'")
		if emp.name not in employee_setup[emp.leave_balance_setup]:
			employee_setup[emp.leave_balance_setup].append({
				'name': emp.name,
				'full_name': emp.full_name,
				'company': emp.company,
				'leave_balance_setup': emp.leave_balance_setup,
				'date_hired': emp.date_hired,
				'regularization_date': None,
			})
		included_employees.append(emp.name)

	#Get leave balance setups
	if setup_included:
		setup_cond = ','.join(setup_included)
		setups = frappe.db.sql(""" SELECT LB.name, LBS.leave_type, LBS.method, LBS.allocation_start, LBS.method_condition, LBS.value, LBS.credits
			FROM `tabLeave Balance Setup` LB INNER JOIN `tabLeave Balance Schedule` LBS ON LBS.`parent` = LB.`name` 
			WHERE LB.`name` IN ("""+setup_cond+""") """, as_dict=1)

	#Get Employee Regularization Date
	if employee_setup:
		reg_date = {}
		empmov = frappe.db.sql(""" SELECT employee, effective_on FROM `tabEmployee Movement` WHERE `movement_type` = 'Regularization' AND docstatus = 1 """, as_dict=1)
		for reg in empmov:
			if reg.employee in included_employees:
				if reg.employee not in reg_date:
					reg_date[reg.employee] = []

				if getdate(reg.effective_on) <= getdate(now_date):
					reg_date[reg.employee].append(reg.effective_on)

		for ems in employee_setup:
			for row in employee_setup[ems]:
				if row['name'] in reg_date:
					if reg_date[row['name']]:
						regularization_date = max(reg_date[row['name']])
						regularization_date = datetime.datetime.strptime(cstr(getdate(regularization_date)), '%Y-%m-%d')
						row['regularization_date'] = regularization_date
	
	#Accumulate LB Entry
	for d in setups:
		for e in employee_setup[d.name]:
			add_credits = 0
			datehired = None
			reference = cstr(d.method)+" from Calendar with "+cstr(d.credits)+" credits"
			#Calendar
			if not d.allocation_start:
				add_credits = check_rundate(d.method, now_date)

			if e['date_hired'] and d.allocation_start in ['Date Hired in Years']:
				reference = cstr(d.method)+" from "+cstr(d.allocation_start)+" "+cstr(d.method_condition)+" "+cstr(d.value)+" with "+cstr(d.credits)+" credits"
				datehired = getdate(e['date_hired'])
				datehired = datetime.datetime.strptime(cstr(getdate(datehired)), '%Y-%m-%d')
				if getdate(datehired) < getdate(now_date):
					year_diff = relativedelta(now_date, datehired).years
					if check_rundate(d.method, now_date):
						if (d.method_condition and d.value):
							add_credits = check_condition(d.method_condition, year_diff, d.value)
						else:
							add_credits = 1

			if e['regularization_date'] and d.allocation_start in ['Regularization in Years']:
				reference = cstr(d.method)+" from "+cstr(d.allocation_start)+" "+cstr(d.method_condition)+" "+cstr(d.value)+" with "+cstr(d.credits)+" credits"
				regular_date = getdate(e['regularization_date'])
				regular_date = datetime.datetime.strptime(cstr(getdate(regular_date)), '%Y-%m-%d')
				if getdate(regular_date) < getdate(now_date):
					year_diff = relativedelta(now_date, regular_date).years
					if check_rundate(d.method, now_date):
						if (d.method_condition and d.value):
							add_credits = check_condition(d.method_condition, year_diff, d.value)
						else:
							add_credits = 1

			if e['regularization_date'] and d.allocation_start in ['Regular']:
				reference = cstr(d.method)+" from "+cstr(d.allocation_start)+" with "+cstr(d.credits)+" credits"
				regular_date = getdate(e['regularization_date'])
				regular_date = datetime.datetime.strptime(cstr(getdate(regular_date)), '%Y-%m-%d')
				if getdate(regular_date) < getdate(now_date):
					year_diff = relativedelta(now_date, regular_date).years
					add_credits = check_rundate(d.method, now_date)

			if add_credits and validate_create_lbentry({'employee': e['name'], 'leave_type': d.leave_type}):
				row = {
					"employee": e['name'],
					"company": e['company'],
					"posting_date": getdate(now_date),
					"leave_type": d.leave_type,
					"balance_type": 'Add',
					"created_from": 'Leave Balance Setup',
					"from_date": getdate(now_date),
					"to_date": year_end,
					"credits": d.credits,
					"linked_document": reference,
				}
				if is_forced:
					row['created_from'] = 'LB Scheduler'
				if validate_duplicate_lbentry(row, is_forced):
					row["employee_name"] = e['full_name']
					row["deduct_credits_to"] = None
					lb = frappe.new_doc("LB Entry")
					lb.update(row)
					lb.flags.ignore_permissions = True
					lb.flags.ignore_validate = True
					if lb.insert():
						lb_entries_created = 1
						if is_forced:
							created_lb_entries += 1

	if is_forced:
		create_lb_entry_logs(created_lb_entries)

	return lb_entries_created

def startfrom_datehired(employee, datehired, method, method_condition, value, yearbased):
	add_credits = 0
	if datehired:
		now_date = nowdate()
		now_date = datetime.datetime.strptime(cstr(getdate(now_date)), '%Y-%m-%d')
		datehired = datetime.datetime.strptime(cstr(getdate(datehired)), '%Y-%m-%d')
		year_diff, year_diff_res, year_diff_date = get_yeardiff(now_date, datehired)

		if method == "Every Month":
			month_diff, month_diff_res, month_diff_date = get_monthdiff(now_date, datehired)
			if getdate(now_date) == getdate(month_diff_date) and getdate(now_date) >= getdate(month_diff_date) and getdate(datehired) != getdate(now_date):
				if yearbased:
					if (method_condition and value):
						add_credits = check_condition(method_condition, year_diff, value)
				else:
					add_credits = 1

		if method == "Every Year":
			if getdate(now_date) == getdate(year_diff_date) and getdate(now_date) >= getdate(year_diff_date) and datehired.year != now_date.year:
				if yearbased:
					if (method_condition and value):
						add_credits = check_condition(method_condition, year_diff, value)
				else:
					add_credits = 1

	return add_credits

def startfrom_regular(employee, method, method_condition, value, yearbased):
	add_credits = 0
	now_date = nowdate()
	now_date = datetime.datetime.strptime(cstr(getdate(now_date)), '%Y-%m-%d')
	reg_date = []
	empmov = frappe.db.sql(""" SELECT effective_on FROM `tabEmployee Movement` WHERE `movement_type` = 'Regularization' AND `employee` = %s """,(employee), as_dict=1)
	for reg in empmov:
		if getdate(reg.effective_on) <= getdate(now_date):
			reg_date.append(reg.effective_on)
	
	if reg_date:
		reg_date = max(reg_date)
		reg_date = datetime.datetime.strptime(cstr(getdate(reg_date)), '%Y-%m-%d')
		year_diff, year_diff_res, year_diff_date = get_yeardiff(now_date, reg_date)
		
		if method == "Every Month":
			month_diff, month_diff_res, month_diff_date = get_monthdiff(now_date, reg_date)
			if getdate(now_date) == getdate(month_diff_date) and getdate(now_date) >= getdate(month_diff_date) and getdate(reg_date) != getdate(now_date):
				if yearbased:
					if (method_condition and value):
						add_credits = check_condition(method_condition, year_diff, value)
				else:
					add_credits = 1

		if method == "Every Year":
			if getdate(now_date) == getdate(year_diff_date) and getdate(now_date) >= getdate(year_diff_date) and reg_date.year != now_date.year:
				if yearbased:
					if (method_condition and value):
						add_credits = check_condition(method_condition, year_diff, value)
				else:
					add_credits = 1

	return add_credits

def validate_create_lbentry(entry, data=None):
	create = 1
	gender, civil_status, is_solo_parent, employment_status, is_active = frappe.db.get_value("Employee", entry['employee'], ["gender", "civil_status", "is_solo_parent", "employment_status", "is_active"])
	is_carry_over, female_only, male_only, married_only, solo_parent_only = frappe.db.get_value("Leave Type", entry['leave_type'], ["is_carry_over", "female_only", "male_only", "married_only", "solo_parent_only"])
	employment_status_setup = frappe.db.sql(""" SELECT employment_status FROM `tabLeave Type Table` WHERE `parent` = %s """,(entry['leave_type']), as_dict=1)
	employment_status_list = []
	for es in employment_status_setup:
		employment_status_list.append(es.employment_status)

	#Validate
	if female_only:
		if gender != "Female":
			create = 0

	if male_only:
		if gender != "Male":
			create = 0

	if married_only:
		if civil_status != "Married":
			create = 0

	if solo_parent_only: 
		if not is_solo_parent:
			create = 0

	if employment_status_list:
		if employment_status not in employment_status_list:
			create = 0

	if not is_active:
		create = 0

	return create

def get_carryover_lvbal():
	result = []
	now_date = nowdate()
	now_date = datetime.datetime.strptime(cstr(getdate(now_date)), '%Y-%m-%d')
	year_end = getdate(datetime.date(datetime.date.today().year, 12, 31))
	pastyear = now_date.year - 1
	pastdate_start = getdate(str(pastyear)+'-01-01')
	pastdate_end = getdate(str(pastyear)+'-12-31')

	if (now_date.day in [1, 01]) and (now_date.month in [1, 01]):
		lb_balance = {}
		lb_entries = frappe.db.sql(""" SELECT * FROM `tabLB Entry` ORDER BY `from_date` ASC """, as_dict=1)
		for d in lb_entries:
			if frappe.get_value("Leave Type", d.leave_type, "is_carry_over"):
				lbid = cstr(d.employee)+cstr(d.leave_type)
				if d.balance_type == 'Less':
					lbid = cstr(d.employee)+cstr(d.deduct_credits_to)

				if lbid not in lb_balance:
					lb_balance[lbid] = {
						"employee": d.employee,
						"leave_type": d.leave_type,
						"balance": 0,
						"valid_entry": [],
						"less_entry": [],
					}

				if d.balance_type == "Add":
					lb_balance[lbid]['valid_entry'].append({
						"employee": d.employee,
						"leave_type": d.leave_type,
						"credits": d.credits,
						"from": getdate(d.from_date),
						"to": getdate(d.to_date),
					})

				if d.balance_type == "Less":
					lb_balance[lbid]['less_entry'].append({
						"employee": d.employee,
						"leave_type": d.leave_type,
						"used": 0,
						"credits": d.credits,
						"from": getdate(d.from_date),
						"to": getdate(d.to_date),
					})

		for e in lb_balance:
			for vl in lb_balance[e]['valid_entry']:
				to_less = 0
				for le in lb_balance[e]['less_entry']:
					if vl['credits'] > 0 and not le['used']:
						if ( vl['from'] <= le['from'] <= vl['to'] ) or ( vl['from'] <= le['to'] <= vl['to'] ):
							to_less += le['credits']
							le['used'] = 1
				vl['credits'] -= to_less
				if ( pastdate_start <= vl['from'] <= pastdate_end ) or ( pastdate_start <= vl['to'] <= pastdate_end )\
				or ( pastdate_end <= vl['from'] <= pastdate_start ) or ( pastdate_end <= vl['to'] <= pastdate_start ):
					lb_balance[e]["balance"] += vl['credits']

			if lb_balance[e]['balance'] > 0:
				result.append({
					"employee": lb_balance[e]["employee"],
					"employee_name": frappe.get_value("Employee", lb_balance[e]["employee"], 'full_name'),
					"posting_date": getdate(now_date),
					"company": frappe.get_value("Employee", lb_balance[e]["employee"], 'company'),
					"leave_type": lb_balance[e]["leave_type"],
					"balance_type": 'Add',
					"created_from": 'Carry Over',
					"from_date": getdate(now_date),
					"to_date": year_end,
					"credits": lb_balance[e]["balance"],
				})

	return result

def validate_duplicate_lbentry(entry, is_forced):
	result = 1
	row = dict(entry)
	row['created_from'] = None
	if entry['created_from'] in ['Leave Balance Setup', 'LB Scheduler']:
		row['created_from'] = ['in', ['Leave Balance Setup', 'LB Scheduler']]
	elif entry['created_from'] in ['Carry Over', 'LB Scheduler - Carry Over']:
		row['created_from'] = ['in', ['Carry Over', 'LB Scheduler - Carry Over']]
		del row['credits']

	lb_list = frappe.db.get_list('LB Entry', filters=row)
	if lb_list:
		result = 0

	if not row['created_from']:
		result = 0

	return result

def create_lb_entry_logs(entry):
	result = []

	full_name = None
	employee_name = frappe.db.get_list('Employee', filters={'user_id': frappe.session.user}, fields=['full_name'])
	if employee_name:
		full_name = employee_name

	logs = frappe.new_doc("Timekeeping Logs")
	logs.update({
		"created_by": frappe.session.user,
		"created_by_name": full_name,
		"button_pressed": 'Force LB Scheduler',
		"number_created": entry,
	})
	logs.flags.ignore_permissions = True
	logs.save()

def holiday_recurring_yearly():
	now_date = nowdate()
	now_date = datetime.datetime.strptime(cstr(getdate(now_date)), '%Y-%m-%d')

	if now_date.day == 01 and now_date.month == 01:
		holidays = frappe.db.sql(""" SELECT * FROM `tabHoliday` WHERE recurring_yearly = 1 AND YEAR(holiday_date) = %s """,(now_date.year-1), as_dict=1)
		if holidays:
			for ho in holidays:
				new_ho = frappe.new_doc("Holiday")
				new_ho.update({
					"holiday_name": ho.holiday_name,
					"holiday_date": getdate(addYears(ho.holiday_date, 1)),
					"is_special": ho.is_special,
					"recurring_yearly": ho.recurring_yearly,
					"description": ho.description,
					"company": ho.company,
					"location": ho.location,
				})
				new_ho.flags.ignore_permissions = True
				try:
					new_ho.save()
				except Exception as e:
					pass

def fix_approved_on_and_by():
	application_type_list = ["Official Business Application", "Leave Application", "Overtime Application", "Change Schedule Application", "Excuse Tardiness Application", "Undertime Application", "Compensatory Time Off", "DTR Problem Application", "Timelogs Application"]
	for app in application_type_list:
		table = "`tab"+app+"`"
		table = str(table)

		if app in ['DTR Problem Application', 'Change Schedule Application', 'Timelogs Application']:
			frappe.db.sql("""UPDATE """+table+""" APP SET APP.`approved_on`=APP.`modified`, APP.`approved_by`=APP.`modified_by`, 
			APP.`approver_name`=(SELECT TE.`full_name` FROM `tabEmployee` TE WHERE TE.`user_id`=APP.modified_by LIMIT 1), APP.`docstatus`=1
			WHERE APP.`workflow_state` IN ('Approved', 'Approval in Progress') AND (APP.approved_on IS NULL OR APP.approved_by IS NULL) """)
		else:
			frappe.db.sql("""UPDATE """+table+""" APP SET APP.`approved_on`=DATE(APP.`modified`), APP.`approved_by`=APP.`modified_by`, 
			APP.`approver_name`=(SELECT TE.`full_name` FROM `tabEmployee` TE WHERE TE.`user_id`=APP.modified_by LIMIT 1), APP.`docstatus`=1
			WHERE APP.`workflow_state` IN ('Approved', 'Approval in Progress') AND (APP.approved_on IS NULL OR APP.approved_by IS NULL) """)