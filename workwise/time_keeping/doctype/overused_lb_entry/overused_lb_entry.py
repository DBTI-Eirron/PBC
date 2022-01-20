# -*- coding: utf-8 -*-
# Copyright (c) 2021, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, calendar
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, cstr, today
from frappe.model.document import Document

class OverusedLBEntry(Document):
	def validate(self):
		total_deduction = 0
		for i in self.get("deduction_history"):
			total_deduction += flt(i.credits)

		self.deducted_credits = total_deduction
		if self.deducted_credits < 0:
			self.deducted_credits = 0
		if total_deduction and self.overused_credits < total_deduction:
			self.deducted_credits = self.overused_credits
		self.remaining_overused_credits = self.overused_credits - self.deducted_credits
		if self.remaining_overused_credits <= 0:
			self.remaining_overused_credits = 0
			self.status = "Cleared"

@frappe.whitelist()
def get_employees_with_overused_credits(employee=None):
	result = []
	data_entry = {}
	data_result = {}
	from_date = nowdate()
	to_date = nowdate()
	included_lawle = []
	leave_applications_without_less_lbentry = get_leave_applications_without_less_lbentry(from_date, to_date)

	if employee:
		query_conditions = "AND LE.employee = '{0}'".format(employee)

	leave_balance = frappe.db.sql(""" SELECT LE.*, TE.full_name
	FROM `tabLB Entry` LE INNER JOIN `tabEmployee` TE ON LE.`employee` = TE.`name` {conditions}
	ORDER BY TE.full_name, LE.creation DESC """.format(conditions=query_conditions), as_dict=1)

	#Init Data
	for lv in leave_balance:
		doc_nam = cstr(lv.employee)+cstr(lv.leave_type)
		if lv.balance_type == 'Less':
			doc_nam = cstr(lv.employee)+cstr(lv.deduct_credits_to)

		if doc_nam not in data_entry:
			data_entry[doc_nam] = {
				"employee": lv.employee,
				"employee_name": cstr(lv.full_name),
				"location": lv.location,
				"leave_type": lv.leave_type,
				"valid_credits": 0,
				"add_entry": [],
				"less_entry": [],
			}

		if lv.balance_type == "Add":
			data_entry[doc_nam]['add_entry'].append({
				"name": lv.name,
				"type": "Add",
				"creation": lv.creation,
				"credits": lv.credits,
				"from_date": getdate(lv.from_date),
				"to_date": getdate(lv.to_date),
				"leave_type": lv.leave_type,
				"deduct_credits_to": None,
				"application": None,
			})
			
		if lv.balance_type == "Less":
			data_entry[doc_nam]['less_entry'].append({
				"name": lv.name,
				"type": "Less",
				"creation": lv.creation,
				"credits": lv.credits,
				"from_date": getdate(lv.from_date),
				"to_date": getdate(lv.to_date),
				"leave_type": lv.leave_type,
				"deduct_credits_to": lv.deduct_credits_to,
				"application": lv.linked_document,
				"included": 0,
			})

	#Process Data
	all_included_less = []
	for dt in data_entry:
		for vl in data_entry[dt]['add_entry']:
			lv_apps_wo_less_amount = 0
			if leave_applications_without_less_lbentry and data_entry[dt]['employee'] in leave_applications_without_less_lbentry:
				if data_entry[dt]['leave_type'] in leave_applications_without_less_lbentry[data_entry[dt]['employee']]:
					lv_apps_wo_less_amount = leave_applications_without_less_lbentry[data_entry[dt]['employee']][data_entry[dt]['leave_type']]

			included_less = []
			if from_date and to_date:
				if ( ( vl['from_date'] <= getdate(from_date) <= vl['to_date'] ) or ( vl['from_date'] <= getdate(to_date) <= vl['to_date'] ) )\
				or ( ( getdate(from_date) <= vl['from_date'] <= getdate(to_date) ) or ( getdate(from_date) <= vl['to_date'] <= getdate(to_date) ) ):
					if dt not in data_result:
				 		data_result[dt] = {
				 			"employee": data_entry[dt]['employee'],
							"employee_name": cstr(data_entry[dt]['employee_name']),
							"location": cstr(data_entry[dt]['location']),
							"leave_type": data_entry[dt]['leave_type'],
							"valid_credits": 0 - lv_apps_wo_less_amount,
							"entry": [],
						}

					data_result[dt]['entry'].append({
						"name": vl['name'],
						"type": vl['type'],
						"creation": vl['creation'],
						"credits": vl['credits'],
						"from_date": vl['from_date'],
						"to_date": vl['to_date'],
						"leave_type": vl['leave_type'],
						"deduct_credits_to": vl['deduct_credits_to'],
						"application": vl['application'],
					})

					to_less = 0
					for le in data_entry[dt]['less_entry']:
						if (vl['credits'] > 0) and not le['included']:
							if (( vl['from_date'] <= le['from_date'] <= vl['to_date'] ) or ( vl['from_date'] <= le['to_date'] <= vl['to_date'] )) \
							or (( le['from_date'] <= vl['from_date'] <= le['to_date'] ) or ( le['from_date'] <= vl['to_date'] <= le['to_date'] )):
								to_less += le['credits']
					 			le['included'] = 1
					 			if le not in all_included_less:
									included_less.append(le)
									all_included_less.append(le)
					vl['credits'] -= to_less
					data_result[dt]['valid_credits'] += vl['credits']
			else:
				if dt not in data_result:
			 		data_result[dt] = {
			 			"employee": data_entry[dt]['employee'],
						"employee_name": cstr(data_entry[dt]['employee_name']),
						"location": cstr(data_entry[dt]['location']),
						"leave_type": data_entry[dt]['leave_type'],
						"valid_credits": 0 - lv_apps_wo_less_amount,
						"entry": [],
					}

				data_result[dt]['entry'].append({
					"name": vl['name'],
					"type": vl['type'],
					"creation": vl['creation'],
					"credits": vl['credits'],
					"from_date": vl['from_date'],
					"to_date": vl['to_date'],
					"leave_type": vl['leave_type'],
					"deduct_credits_to": vl['deduct_credits_to'],
					"application": vl['application'],
				})

				to_less = 0
				for le in data_entry[dt]['less_entry']:
					if (vl['credits'] > 0) and not le['included']:
						if (( vl['from_date'] <= le['from_date'] <= vl['to_date'] ) or ( vl['from_date'] <= le['to_date'] <= vl['to_date'] )) \
						or (( le['from_date'] <= vl['from_date'] <= le['to_date'] ) or ( le['from_date'] <= vl['to_date'] <= le['to_date'] )):
							to_less += le['credits']
				 			le['included'] = 1
				 			if le not in all_included_less:
								included_less.append(le)
								all_included_less.append(le)
				vl['credits'] -= to_less
				data_result[dt]['valid_credits'] += vl['credits']

	for dr in data_result:
		if data_result[dr]['valid_credits'] < 0:
			result.append({
				"employee": data_result[dr]['employee'],
				"leave_type": data_result[dr]['leave_type'],
				"credits": data_result[dr]['valid_credits'],
			})

	if leave_applications_without_less_lbentry:
		for lawll_employee in leave_applications_without_less_lbentry:
			for lawll_lvtype in leave_applications_without_less_lbentry[lawll_employee]:
				if not (filter(lambda d: lawll_employee == d.get('employee') and lawll_lvtype == d.get('leave_type'), result)):
					result.append({
						"employee": lawll_employee,
						"leave_type": lawll_lvtype,
						"credits": leave_applications_without_less_lbentry[lawll_employee][lawll_lvtype],
					})

	return result

def create_overused_entry_for_employees():
	employees_with_overused_credits = get_employees_with_overused_credits()
	if employees_with_overused_credits:
		for i in employees_with_overused_credits:
			doc = frappe.new_doc("Overused LB Entry")
			doc_data = {
				"employee": i.get("employee"),
				"employee_name": frappe.db.get_value("Employee", i.get("employee"), "full_name"),
				"company": frappe.db.get_value("Employee", i.get("employee"), "company"),
				"status": "Pending",
				"overused_credits": abs(i.get("credits")),
				"leave_type": i.get("leave_type"),
				"deducted_credits": 0,
				"remaining_overused_credits": abs(i.get("credits"))
			}
			doc.update(doc_data)
			doc.flags.ignore_permissions = True
			if not validate_overuse_if_exists(doc_data):
				doc.insert()

def get_leave_applications_without_less_lbentry(from_date, to_date, with_application_data=0):
	result = {}
	with_application_data_result = {}
	range_from_date = None
	range_to_date = None
	py_list = frappe.get_all('Payroll Year', fields=['name', 'from_date', 'to_date'])
	for pay_year in py_list:
		if getdate(pay_year.from_date) <= getdate(from_date) <= getdate(pay_year.to_date) or getdate(pay_year.from_date) <= getdate(to_date) <= getdate(pay_year.to_date):
			range_from_date = getdate(pay_year.from_date)
			range_to_date = getdate(pay_year.to_date)

	if range_from_date and range_to_date:
		lv_list = frappe.get_all('Leave Application', filters={'linked_lb_entry': None, 'workflow_state': 'Approved'}, fields=['name', 'employee', 'leave_type', 'total_leave_days', 'from_date', 'to_date', 'linked_lb_entry'])
		for lv in lv_list:
			if not lv.linked_lb_entry:
				if range_from_date <= getdate(lv.from_date) <= range_to_date or range_from_date <= getdate(lv.to_date) <= range_to_date:
					deduct_credits_to = lv.leave_type
					deduct_to = frappe.db.get_value("Leave Type", lv.leave_type, "deduct_to")
					if deduct_to:
						deduct_credits_to = deduct_to

					if lv.employee not in result:
						result[lv.employee] = {}
						with_application_data_result[lv.employee] = {}

					if deduct_credits_to not in result[lv.employee]:
						result[lv.employee][deduct_credits_to] = 0

					if lv.name not in with_application_data_result[lv.employee]:
						with_application_data_result[lv.employee][lv.name] = {
							'name': lv.name,
							'total_leave_days': lv.total_leave_days,
							'from_date': lv.from_date,
							'to_date': lv.to_date,
						}

					result[lv.employee][deduct_credits_to] += flt(lv.total_leave_days, 2)

	if with_application_data:
		return with_application_data_result
	else:
		return result

def validate_overuse_if_exists(overuse_data):
	result = None
	ole_list = frappe.get_all('Overused LB Entry', filters={'employee': overuse_data.get('employee'), 'leave_type': overuse_data.get('leave_type')}, fields=['name'])
	if ole_list:
		result = True
		more_than_one = 0
		if len(ole_list) > 1:
			more_than_one = 1
		for ole in ole_list:
			doc = frappe.get_doc('Overused LB Entry', ole.name)
			total_overused_credits = 0
			overuse_data_overused_credits = flt(overuse_data.get("overused_credits"), 2)
			doc_overused_credits = flt(doc.overused_credits, 2)
			new_remaining_overused_credits = 0
			to_update_doc = 0
			new_status = None

			if overuse_data_overused_credits != doc_overused_credits:
				total_overused_credits = abs( overuse_data_overused_credits )
				to_update_doc = 1
				new_status = "Pending"
				new_remaining_overused_credits = total_overused_credits - doc.deducted_credits

			if to_update_doc:
				frappe.db.set_value('Overused LB Entry', ole.name, 'status',  new_status if new_status else doc.get("status") )
				frappe.db.set_value('Overused LB Entry', ole.name, 'overused_credits', total_overused_credits )
				frappe.db.set_value('Overused LB Entry', ole.name, 'remaining_overused_credits', new_remaining_overused_credits if new_remaining_overused_credits else doc.get("remaining_overused_credits") )

		if more_than_one:
			print(more_than_one)

	return result

def deduct_no_linked_lb_entry_to_overuse():
	from_date = nowdate()
	to_date = nowdate()
	leave_applications_without_less_lbentry = get_leave_applications_without_less_lbentry(from_date, to_date)
	if leave_applications_without_less_lbentry:
		for emp in leave_applications_without_less_lbentry:
			for leave_type in leave_applications_without_less_lbentry[emp]:
				doc_list = frappe.get_all('Overused LB Entry', filters={'employee': emp, 'leave_type': leave_type}, fields=['name'])
				for doc in doc_list:
					doc = frappe.get_doc('Overused LB Entry', doc.name)

					creds_value = leave_applications_without_less_lbentry[emp][leave_type]

					for ded_h in doc.get("deduction_history"):
						lb_entry_doc = frappe.get_doc('LB Entry', ded_h.lb_entry)
						creds_value = creds_value + lb_entry_doc.credits

					new_deducted_credits = creds_value
					if doc.overused_credits < creds_value:
						new_deducted_credits = doc.overused_credits

					new_remaining_overused_credits = doc.overused_credits - new_deducted_credits
					if new_remaining_overused_credits < 0:
						new_remaining_overused_credits = 0

					new_status = "Cleared"
					if new_remaining_overused_credits:
						new_status = "Pending"

					frappe.db.set_value( 'Overused LB Entry', doc.name, 'deducted_credits', new_deducted_credits )
					frappe.db.set_value( 'Overused LB Entry', doc.name, 'remaining_overused_credits', new_remaining_overused_credits )
					frappe.db.set_value( 'Overused LB Entry', doc.name, 'status', new_status )

def recalculate_credits():
	doc_list = frappe.get_all('Overused LB Entry', fields=['name'])
	for doc in doc_list:
		doc = frappe.get_doc('Overused LB Entry', doc.name)
		creds_value = 0
		for ded_h in doc.get("deduction_history"):
			lb_entry_doc = frappe.get_doc('LB Entry', ded_h.lb_entry)
			creds_value = creds_value + lb_entry_doc.credits

		new_deducted_credits = creds_value
		if doc.overused_credits < creds_value:
			new_deducted_credits = doc.overused_credits

		new_remaining_overused_credits = doc.overused_credits - new_deducted_credits
		if new_remaining_overused_credits < 0:
			new_remaining_overused_credits = 0

		new_status = "Cleared"
		if new_remaining_overused_credits:
			new_status = "Pending"

		frappe.db.set_value( 'Overused LB Entry', doc.name, 'deducted_credits', new_deducted_credits )
		frappe.db.set_value( 'Overused LB Entry', doc.name, 'remaining_overused_credits', new_remaining_overused_credits )
		frappe.db.set_value( 'Overused LB Entry', doc.name, 'status', new_status )


def re_generate_overuse(as_of_date=None, employee='1508'):
	data = []
	data_entry = {}
	data_result = {}
	data_per_add_entry = {}

	if not as_of_date:
		as_of_date = nowdate()
	from_date = getdate(as_of_date)
	to_date = getdate(as_of_date)
	overuse_lb_entries = get_overuse_lb_entries()
	payroll_year = frappe.get_all("Payroll Year", filters={'from_date': ('>=', from_date), 'to_date': ('<=', from_date)}, fields=['from_date', 'to_date'])
	if payroll_year:
		from_date = getdate(payroll_year.from_date)
		to_date = getdate(payroll_year.to_date)

	leave_balance = frappe.db.sql(""" SELECT LE.*, TE.full_name, TE.`location`
		FROM `tabLB Entry` LE INNER JOIN `tabEmployee` TE ON LE.`employee` = TE.`name` 
		INNER JOIN `tabLocation` LOC ON TE.`location` = LOC.`name`
		ORDER BY TE.full_name, LE.creation DESC """.format(conditions=get_conditions(employee)), as_dict=1)

	#Init Data
	for lv in leave_balance:
		doc_nam = cstr(lv.employee)+cstr(lv.leave_type)
		if lv.balance_type == 'Less':
			doc_nam = cstr(lv.employee)+cstr(lv.deduct_credits_to)

		if doc_nam not in data_entry:
			data_entry[doc_nam] = {
				"employee":  lv.employee,
				"employee_name": cstr(lv.full_name),
				"location": lv.location,
				"valid_credits": 0,
				"add_entry": [],
				"less_entry": [],
			}

		if lv.balance_type == "Add":
			data_entry[doc_nam]['add_entry'].append({
				"name": lv.name,
				"employee":  lv.employee,
				"employee_name": cstr(lv.full_name),
				"type": "Add",
				"creation": lv.creation,
				"credits": lv.credits,
				"original_credits": lv.credits,
				"from_date": getdate(lv.from_date),
				"to_date": getdate(lv.to_date),
				"leave_type": lv.leave_type,
				"deduct_credits_to": None,
				"application": None,
			})
			
		if lv.balance_type == "Less":
			data_entry[doc_nam]['less_entry'].append({
				"name": lv.name,
				"employee":  lv.employee,
				"employee_name": cstr(lv.full_name),
				"type": "Less",
				"creation": lv.creation,
				"credits": lv.credits,
				"original_credits": lv.credits,
				"from_date": getdate(lv.from_date),
				"to_date": getdate(lv.to_date),
				"leave_type": lv.leave_type,
				"deduct_credits_to": lv.deduct_credits_to,
				"application": lv.linked_document,
				"included": 0,
			})

	#Process Data
	all_included_less = []
	for dt in data_entry:
		for vl in data_entry[dt]['add_entry']:
			included_less = []
			if vl['employee'] not in data_per_add_entry:
				data_per_add_entry[vl['employee']] = {}
			if vl['leave_type'] not in data_per_add_entry[vl['employee']]:
				data_per_add_entry[vl['employee']][vl['leave_type']] = {
					"total_balance": 0,
					"included_less": {}
				}
			if vl['name'] not in data_per_add_entry[vl['employee']][vl['leave_type']]['included_less']:
				data_per_add_entry[vl['employee']][vl['leave_type']]['included_less'][vl['name']] = {
					"data": None,
					"balance": 0,
					"included_less": []
				}
			data_per_add_entry[vl['employee']][vl['leave_type']]['included_less'][vl['name']]['data'] = vl

			if dt not in data_result:
		 		data_result[dt] = {
					"employee_name": cstr(data_entry[dt]['employee_name']),
					"location": cstr(data_entry[dt]['location']),
					"valid_credits": 0,
					"entry": [],
				}
			data_result[dt]['entry'].append({
				"type": vl['type'],
				"creation": vl['creation'],
				"credits": vl['credits'],
				"from_date": vl['from_date'],
				"to_date": vl['to_date'],
				"leave_type": vl['leave_type'],
				"deduct_credits_to": vl['deduct_credits_to'],
				"application": vl['application'],
			})

			to_less = 0
			for le in data_entry[dt]['less_entry']:
				if (vl['credits'] > 0) and not le['included']:
					if (( vl['from_date'] <= le['from_date'] <= vl['to_date'] ) or ( vl['from_date'] <= le['to_date'] <= vl['to_date'] )) \
					or (( le['from_date'] <= vl['from_date'] <= le['to_date'] ) or ( le['from_date'] <= vl['to_date'] <= le['to_date'] )):
						if le not in data_per_add_entry[vl['employee']][vl['leave_type']]['included_less'][vl['name']]['included_less']:
							data_per_add_entry[vl['employee']][vl['leave_type']]['included_less'][vl['name']]['included_less'].append(le)
						to_less += le['credits']
			 			le['included'] = 1
			 			if le not in all_included_less:
							included_less.append(le)
							all_included_less.append(le)

			vl['credits'] -= to_less
			data_per_add_entry[vl['employee']][vl['leave_type']]['included_less'][vl['name']]["balance"] = vl['credits']
			data_result[dt]['valid_credits'] += vl['credits']

			for inc in included_less:
				if dt in data_result:
					data_result[dt]['entry'].append(inc)

	#Generate Data
	for employee in data_per_add_entry:
		for lv_type in data_per_add_entry[employee]:
			total_add_entry_balance = 0
			inlucded = 0
			stacked_actual_overused = 0
			stacked_remaining_overused = 0
			for add_entry in data_per_add_entry[employee][lv_type]['included_less']:
				add_entry_balance = data_per_add_entry[employee][lv_type]['included_less'][add_entry]['balance']
				add_entry_data = data_per_add_entry[employee][lv_type]['included_less'][add_entry]['data']
				if str(add_entry_data.get("name")) in overuse_lb_entries:
					add_entry_balance -= overuse_lb_entries[add_entry_data.get("name")]

				if ( ( getdate(add_entry_data.get("from_date")) <= getdate(from_date) <= getdate(add_entry_data.get("to_date")) ) or \
					( getdate(add_entry_data.get("from_date")) <= getdate(to_date) <= getdate(add_entry_data.get("to_date")) ) ) or \
					( ( getdate(from_date) <= getdate(add_entry_data.get("from_date")) <= getdate(to_date) ) or \
					( getdate(from_date) <= getdate(add_entry_data.get("to_date")) <= getdate(to_date) ) ):
					inlucded = 1

					#Remaining Balance
					total_add_entry_balance += add_entry_balance
					if add_entry_balance < 0:
						remaining_overused = add_entry_balance
						actual_overused = add_entry_balance
						if add_entry_data.get("name") in overuse_lb_entries:
							actual_overused += overuse_lb_entries[add_entry_data.get("name")]
						#raise Exception( overuse_lb_entries )
						stacked_actual_overused += actual_overused
						stacked_remaining_overused += remaining_overused
						add_entry_data.update({'actual_overused': actual_overused, 'remaining_overused': remaining_overused})
			
			#OVERUSE
			if stacked_remaining_overused:
				new_overused(employee, lv_type, stacked_actual_overused, stacked_remaining_overused)

			#Total Remaining Balance
			if inlucded:
				total_add_entry_balance


def new_overused(employee, lv_type, stacked_actual_overused, stacked_remaining_overused):
	#check if existing
	getall_filters = {}
	getall_filters["employee"] = employee
	getall_filters["leave_type"] = lv_type

	olbe_list = frappe.get_all('Overused LB Entry', filters=getall_filters, fields=['name'])
	for olbe in olbe_list:
		doc = frappe.get_doc('Overused LB Entry', olbe.name)

def get_conditions(employee=None):
	conditions = ""
	if employee:
		conditions = "WHERE LE.`employee`=%(employee)s"

	return conditions

def get_overuse_lb_entries():
	result = {}
	olbe_list = frappe.get_all('Overused LB Entry', fields=['name'])
	for olbe in olbe_list:
		doc = frappe.get_doc('Overused LB Entry', olbe.name)
		for row in doc.get('deduction_history'):
			if row.lb_entry not in result:
				result[row.lb_entry] = 0
			result[row.lb_entry] += row.credits

	return result

def create_less_lbentry_for_leave_applications_without_linked_lb_entry():
	generated_result = None
	leave_applications_without_less_lbentry = get_leave_applications_without_less_lbentry(from_date=nowdate(), to_date=nowdate(), with_application_data=1)
	if leave_applications_without_less_lbentry:
		for employee in leave_applications_without_less_lbentry:
			for leave_application in leave_applications_without_less_lbentry[employee]:
				application_data = frappe.get_doc('Leave Application', leave_application)
				deduct_credits_to = application_data.get('leave_type')
				deduct_to = frappe.db.get_value("Leave Type", application_data.get('leave_type'), "deduct_to")
				if deduct_to:
					deduct_credits_to = deduct_to
				row_entry = {
					"employee": application_data.get('employee'),
					"employee_name": application_data.get('full_name'),
					"posting_date": application_data.get('posting_date'),
					"company": application_data.get('company'),
					"leave_type": application_data.get('leave_type'),
					"balance_type": 'Less',
					"created_from": 'Leave Application',
					"linked_document": application_data.get('name'),
					"from_date": application_data.get('from_date'),
					"to_date": application_data.get('to_date'),
					"credits": application_data.get('total_leave_days'),
					"deduct_credits_to": deduct_credits_to,
				}
				if not frappe.get_all("LB Entry", filters=row_entry):
					lb = frappe.new_doc("LB Entry")
					lb.created_from_no_linked_leave_applications = 1
					lb.update(row_entry)
					lb.flags.ignore_permissions = True
					if lb.insert():
						frappe.db.sql("""UPDATE `tabLeave Application` SET linked_lb_entry = %s WHERE name = %s""",(lb.name, leave_application))
						if not generated_result:
							generated_result = ""
						generated_result += 'Created Less LB Entry({0}) for Leave Application ({1}) \n'.format(lb.name, leave_application)

	if generated_result:
		create_txt_file(generated_result, 'created_less_lb_entries')

def create_txt_file(file_content, file_name):
	import frappe
	from frappe.utils import now, get_site_name

	now = str(now())
	now = now[0: -10]
	file_name = now+'_'+str(file_name)
	file_name = file_name.replace('-', '')
	file_name = file_name.replace(':', '')
	file_name = file_name.replace(' ', '_')
	file_name = file_name+".txt"
	public_file_path = frappe.get_site_path('public', 'files', file_name)
	file = open(public_file_path, 'w')
	file.write(file_content)
	file.close()

	return public_file_path