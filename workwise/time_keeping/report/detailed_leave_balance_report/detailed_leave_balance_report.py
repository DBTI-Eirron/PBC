# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import date
from frappe import _
from frappe.utils import getdate, cstr, flt, nowdate

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)

	return result

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "leave_type",
			"label": _("Leave Type"),
			"fieldtype": "Link",
			"options": "Leave Type",
			"width": 200
		},
		{
			"fieldname": "credits",
			"label": _("Credits"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "from_date",
			"label": _("From Date"),
			"fieldtype": "Date",
			"width": 140
		},
		{
			"fieldname": "to_date",
			"label": _("To Date"),
			"fieldtype": "Date",
			"width": 140
		},
		{
			"fieldname": "type",
			"label": _("Type"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "deduct_to",
			"label": _("Deduct To"),
			"fieldtype": "Link",
			"options": "Leave Type",
			"width": 160
		},
		{
			"fieldname": "used_in",
			"label": _("Used In"),
			"fieldtype": "Link",
			"options": "Leave Application",
			"width": 200
		},
	]

	return columns
		
def get_data(filters, generate_overuse=0, balance_only=0, summary_only=0):
	balance = 0
	generate_overuse_data = {}
	remaining_balance_data = {}
	summary_only_data = {}
	balance_only_data = {'balance': 0, 'from_balance': '', 'original_credits': 0}
	data = []
	data_entry = {}
	data_result = {}
	data_per_add_entry = {}
	sorted_by = ['employee_name']
	location_included = [filters.location]

	from_date = getdate(filters.as_of_date)
	to_date = getdate(filters.as_of_date)
	leave_applications_without_less_lbentry, inluded_from_balance = get_leave_applications_without_less_lbentry(from_date, to_date)
	overuse_lb_entries = get_overuse_lb_entries()
	payroll_year = frappe.get_all("Payroll Year", filters={'from_date': ('>=', from_date), 'to_date': ('<=', from_date)}, fields=['from_date', 'to_date'])
	if payroll_year:
		from_date = getdate(payroll_year.from_date)
		to_date = getdate(payroll_year.to_date)

	data.append({ "employee_name":"<b>Company: </b>"+filters.company })
	if filters.location:
		sorted_by.insert(0, 'location')
		data.append({ "employee_name":"<b>Location: </b>"+filters.location })
	data.append({})

	leave_balance = frappe.db.sql(""" SELECT LE.*, TE.full_name, TE.`location`
		FROM `tabLB Entry` LE INNER JOIN `tabEmployee` TE ON LE.`employee` = TE.`name` 
		INNER JOIN `tabLocation` LOC ON TE.`location` = LOC.`name`
		WHERE TE.`company` = %(company)s {conditions} ORDER BY TE.full_name, LE.creation DESC """.format(conditions=get_conditions(filters)), filters, as_dict=1)

	#Init Data
	for lv in leave_balance:
		if lv.company == filters.company:
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
					"created_from": lv.created_from,
					"application": lv.linked_document,
					"included": 0
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
						le_included = 0
						if le not in data_per_add_entry[vl['employee']][vl['leave_type']]['included_less'][vl['name']]['included_less']:
							if le['application'] and le['created_from'] and le['created_from'] == 'Leave Application':
								from_balance = frappe.db.get_value('Leave Application', le['application'], "from_balance")
								if str(vl['name']) in str(from_balance):
									data_per_add_entry[vl['employee']][vl['leave_type']]['included_less'][vl['name']]['included_less'].append(le)
									le_included = 1
							else:
								data_per_add_entry[vl['employee']][vl['leave_type']]['included_less'][vl['name']]['included_less'].append(le)
								le_included = 1
						if le_included:
							to_less += le['credits']
				 			le['included'] = le_included
				 			if le not in all_included_less:
								included_less.append(le)
								all_included_less.append(le)
			vl['credits'] -= to_less
			data_per_add_entry[vl['employee']][vl['leave_type']]['included_less'][vl['name']]["balance"] = vl['credits']
			data_result[dt]['valid_credits'] += vl['credits']

			for inc in included_less:
				if dt in data_result:
					data_result[dt]['entry'].append(inc)
	cid = []
	#Generate Data
	for employee in data_per_add_entry:
		for lv_type in data_per_add_entry[employee]:
			total_add_entry_balance = 0
			balance_with_deducted_overuse = 0
			negative_balance = 0
			positive_balance = 0
			balance = 0
			deducted_overuse_balance = 0
			inlucded = 0
			
			#Overuse Data Generation Init
			if employee not in generate_overuse_data:
				generate_overuse_data[employee] = {}
			if lv_type not in generate_overuse_data[employee]:
				generate_overuse_data[employee][lv_type] = {
					'stacked_overused': 0,
					'stacked_remaining_overused': 0,
					'stacked_cleared_overused': 0,
				}
			#Init Remaining Balance Data
			if employee not in remaining_balance_data:
				remaining_balance_data[employee] = {}
			if lv_type not in remaining_balance_data[employee]:
				remaining_balance_data[employee][lv_type] = {
					"remainig_balance": 0,
					"included_add_entries": []
				}

			if employee not in summary_only_data:
				summary_only_data[employee] = {}
			if lv_type not in summary_only_data[employee]:
				summary_only_data[employee][lv_type] = {
					'original_credits': 0,
					'remaining_balance': 0
				}

			for add_entry in data_per_add_entry[employee][lv_type]['included_less']:
				add_entry_balance = data_per_add_entry[employee][lv_type]['included_less'][add_entry]['balance']
				add_entry_data = data_per_add_entry[employee][lv_type]['included_less'][add_entry]['data']
				stacked_add_entry_balance = flt(add_entry_balance)
				balance_with_deducted_overuse = add_entry_balance
				if add_entry_data.get("name") in overuse_lb_entries:
					stacked_add_entry_balance -= overuse_lb_entries[add_entry_data.get("name")]
					if balance_with_deducted_overuse > overuse_lb_entries[add_entry_data.get("name")]:
						balance_with_deducted_overuse -= overuse_lb_entries[add_entry_data.get("name")]
					generate_overuse_data[employee][lv_type]['stacked_cleared_overused'] += overuse_lb_entries[add_entry_data.get("name")]
				generate_overuse_data[employee][lv_type]['stacked_remaining_overused'] += stacked_add_entry_balance

				if ( ( getdate(add_entry_data.get("from_date")) <= getdate(from_date) <= getdate(add_entry_data.get("to_date")) ) or \
					( getdate(add_entry_data.get("from_date")) <= getdate(to_date) <= getdate(add_entry_data.get("to_date")) ) ) or \
					( ( getdate(from_date) <= getdate(add_entry_data.get("from_date")) <= getdate(to_date) ) or \
					( getdate(from_date) <= getdate(add_entry_data.get("to_date")) <= getdate(to_date) ) ):
					inlucded = 1
					row = {
						"employee_name": add_entry_data.get("employee_name"),
						"leave_type": add_entry_data.get("leave_type"),
						"type": add_entry_data.get("type"),
						"from_date": add_entry_data.get("from_date"),
						"to_date": add_entry_data.get("to_date"),
						"credits": add_entry_data.get("original_credits"),
						"used_in": add_entry_data.get("application"),
						"deduct_to": add_entry_data.get("deduct_credits_to"),
					}
					data.append(row)
					balance_only_data['original_credits'] += add_entry_data.get("original_credits")
					summary_only_data[employee][lv_type]['original_credits'] += add_entry_data.get("original_credits")
					if data_per_add_entry[employee][lv_type]['included_less'][add_entry]['included_less']:
						for less_entry in data_per_add_entry[employee][lv_type]['included_less'][add_entry]['included_less']:
							row = {
								"employee_name": less_entry.get("employee_name"),
								"leave_type": less_entry.get("leave_type"),
								"type": less_entry.get("type"),
								"from_date": less_entry.get("from_date"),
								"to_date": less_entry.get("to_date"),
								"credits": less_entry.get("original_credits"),
								"used_in": less_entry.get("application"),
								"deduct_to": less_entry.get("deduct_credits_to"),
							}
							data.append(row)
					#Remaining Balance
					total_add_entry_balance += balance_with_deducted_overuse
					view_negative_entry_balance = add_entry_balance
					if add_entry_balance < 0:
						negative_balance += add_entry_balance
						generate_overuse_data[employee][lv_type]['stacked_overused'] += abs(flt(add_entry_balance))
					if balance_with_deducted_overuse > 0:
						remaining_balance_data[employee][lv_type]['remainig_balance'] += balance_with_deducted_overuse
						remaining_balance_data[employee][lv_type]['included_add_entries'].append(add_entry_data)
						balance_only_data['from_balance'] += str(add_entry_data.get("name"))
					
					view_add_entry_balance = add_entry_balance
					if not filters.allow_negative and add_entry_balance < 0:
						view_add_entry_balance = 0
					positive_balance += add_entry_balance

					data.append({
						"employee_name": "",
						"leave_type": "<b>Remaining Balance",
						"credits": view_add_entry_balance,
						"type": "</b>",
						"from_date": "",
						"to_date": "",
						"used_in": "",
						"deduct_to": "",
					})
					if add_entry_data.get("name") in overuse_lb_entries:
						deducted_overuse_balance += overuse_lb_entries[add_entry_data.get("name")]
						data.append({
							"employee_name": "",
							"leave_type": "<b>Deducted Overused Credits",
							"credits": overuse_lb_entries[add_entry_data.get("name")],
							"type": "</b>",
							"from_date": "",
							"to_date": "",
							"used_in": "",
							"deduct_to": "",
						})
			#Total Remaining Balance
			if inlucded:
				total_add_entry_balance = positive_balance - (negative_balance + deducted_overuse_balance)
				if positive_balance <= 0:
					total_add_entry_balance = positive_balance
				if not filters.allow_negative and total_add_entry_balance < 0:
					total_add_entry_balance = 0
				balance = total_add_entry_balance
				summary_only_data[employee][lv_type]['remaining_balance'] += total_add_entry_balance
				data.append({
					"employee_name": "",
					"leave_type": "<b>Total Remaining Balance",
					"credits": total_add_entry_balance,
					"type": "</b>",
					"from_date": "",
					"to_date": "",
					"used_in": "",
					"deduct_to": "",
				})
				data.append({})
				#OVERUSE
				overused_lb_entries = get_overused_lb_entries(employee, lv_type)
				if overused_lb_entries:
					data.extend(overused_lb_entries)
					data.append({})

	if generate_overuse:
		generate_new_overuse(generate_overuse_data, remaining_balance_data)
	if not balance_only and not summary_only:
		return data
	if balance_only:
		balance_only_data['balance'] = balance
		return balance_only_data
	if summary_only:
		return summary_only_data

def get_leave_balance_via_detailed_balance_report(company, employee, leave_type, as_of_date):
	filters = frappe._dict({
		"company": company,
		"as_of_date": as_of_date,
		"location": None,
		"employee": employee,
		"leave_type": leave_type,
		"period_group": None,
		"allow_negative": 1
	})
	result = get_data(filters, balance_only=1)
	return result

def get_leave_balance_summary_via_detailed_balance_report(company, as_of_date, employee=None):
	filters = frappe._dict({
		"company": company,
		"as_of_date": as_of_date,
		"location": None,
		"employee": employee,
		"leave_type": None,
		"period_group": None,
		"allow_negative": 1
	})

	result = get_data(filters, summary_only=1)
	return result

def generate_overuse_via_detailed_balance_report():
	company_list = frappe.get_all('Company', fields=['name'])
	for company in company_list:
		company = company.name
		filters = frappe._dict({
			"company": company,
			"as_of_date": nowdate(),
			"location": None,
			"employee": None,
			"leave_type": None,
			"period_group": None,
			"allow_negative": None
		})
		get_data(filters, generate_overuse=1)

def generate_new_overuse(data, remaining_balance_data):
	for employee in data:
		for lv_type in data[employee]:
			doc_list = frappe.get_all('Overused LB Entry', filters={'employee': employee, 'leave_type': lv_type}, fields=['name'])
			if not doc_list:
				if data[employee][lv_type]['stacked_overused']:
					doc = frappe.new_doc('Overused LB Entry')
					doc.employee = employee
					doc.employee_name = frappe.db.get_value("Employee", employee, "full_name")
					doc.company = frappe.db.get_value("Employee", employee, "company")
					doc.status = "Pending"
					doc.leave_type = lv_type
					doc.overused_credits = data[employee][lv_type]['stacked_overused']
					doc.deducted_credits = 0
					doc.remaining_overused_credits = data[employee][lv_type]['stacked_overused']
					doc.flags.ignore_permissions = True
					doc.save()
			else:
				for doc in doc_list:
					doc = frappe.get_doc('Overused LB Entry', doc.name)
					to_update = 0
					doc_overused_credits = doc.overused_credits
					doc_remaining_overused_credits = doc.remaining_overused_credits
					doc_deducted_credits = doc_overused_credits - doc_remaining_overused_credits
					stacked_overused = data[employee][lv_type]['stacked_overused']
					stacked_cleared_overused = data[employee][lv_type]['stacked_cleared_overused']
					stacked_remaining_overused = data[employee][lv_type]['stacked_remaining_overused']
					overused_deduction_history = []
					current_doc_deducted_credits = 0
					for row in doc.get('deduction_history'):
						current_doc_deducted_credits += row.credits
						overused_deduction_history.append(row.lb_entry)
					doc_deducted_credits = current_doc_deducted_credits

					new_remaining_overused_credits = stacked_overused - doc_deducted_credits
					if new_remaining_overused_credits > 0:
						if employee in remaining_balance_data:
							if lv_type in remaining_balance_data[employee]:
								for included_add_entry in remaining_balance_data[employee][lv_type]['included_add_entries']:
									if included_add_entry.get("name") not in overused_deduction_history:
										if included_add_entry.get('credits') > 0 and new_remaining_overused_credits > 0:
											new_deducted_credits = min(new_remaining_overused_credits, included_add_entry.get('credits'))
											new_remaining_overused_credits -= new_deducted_credits
											doc.append('deduction_history', {
												'lb_entry': included_add_entry.get("name"),
												'credits': abs(new_deducted_credits)
											})
											doc.flags.ignore_permissions = True
											doc.save()

					#update overuse credits
					if stacked_overused > 0:
						frappe.db.set_value( 'Overused LB Entry', doc.name, 'overused_credits', stacked_overused )
					#update deduction credits
					new_doc = frappe.get_doc('Overused LB Entry', doc.name)
					new_deducted_credits = 0
					for new_deduction in new_doc.get('deduction_history'):
						new_deducted_credits += new_deduction.credits
					frappe.db.set_value( 'Overused LB Entry', doc.name, 'deducted_credits', new_deducted_credits )
					#update remaining overuse credits
					latest_overused_credits = frappe.db.get_value('Overused LB Entry', doc.name, "overused_credits")
					latest_deducted_credits = frappe.db.get_value('Overused LB Entry', doc.name, "deducted_credits")
					new_remaining_overused_credits = latest_overused_credits - latest_deducted_credits	
					new_status = "Cleared"
					if new_remaining_overused_credits > 0:
						new_status = "Pending"
					else:
						new_remaining_overused_credits = 0
					frappe.db.set_value( 'Overused LB Entry', doc.name, 'remaining_overused_credits', new_remaining_overused_credits )
					frappe.db.set_value( 'Overused LB Entry', doc.name, 'status', new_status )

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("LE.`employee`=%(employee)s")

	if filters.location:
		conditions.append("TE.`location`=%(location)s")

	if filters.get("leave_type"):
		conditions.append("(LE.`leave_type`=%(leave_type)s OR LE.`deduct_credits_to`=%(leave_type)s)")

	if filters.get("period_group"):
		conditions.append("TE.period_group='{0}'".format(filters.get("period_group")))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

def get_overused_lb_entries(employee, leave_type):
	result = None
	ole_list = frappe.get_all('Overused LB Entry', filters={'employee': employee,'leave_type': leave_type}, fields=['name'])
	for ole in ole_list:
		doc = frappe.get_doc('Overused LB Entry', ole.name)
		result = [
			{
				"employee_name": "",
				"leave_type": "<b>Total Overused Credits",
				"credits": doc.get("overused_credits"),
				"type": "</b>",
				"from_date": "",
				"to_date": "",
				"used_in": "",
				"deduct_to": "",
			},
			{
				"employee_name": "",
				"leave_type": "<b>Cleared Overused Credits",
				"credits": doc.get("deducted_credits"),
				"type": "</b>",
				"from_date": "",
				"to_date": "",
				"used_in": "",
				"deduct_to": "",
			},
			{
				"employee_name": "",
				"leave_type": "<b>Remaining Overused Credits",
				"credits": doc.get("overused_credits") - doc.get("deducted_credits"),
				"type": "</b>",
				"from_date": "",
				"to_date": "",
				"used_in": "",
				"deduct_to": "",
			}
		]

	return result

def get_leave_applications_without_less_lbentry(from_date, to_date):
	inluded_from_balance = []
	result = {}
	range_from_date = None
	range_to_date = None
	py_list = frappe.get_all('Payroll Year', fields=['name', 'from_date', 'to_date'])
	for pay_year in py_list:
		if getdate(pay_year.from_date) <= getdate(from_date) <= getdate(pay_year.to_date) or getdate(pay_year.from_date) <= getdate(to_date) <= getdate(pay_year.to_date):
			range_from_date = getdate(pay_year.from_date)
			range_to_date = getdate(pay_year.to_date)

	if range_from_date and range_to_date:
		lv_list = frappe.get_all('Leave Application', filters={'linked_lb_entry': None, 'workflow_state': 'Approved'}, fields=['name', 'employee', 'leave_type', 'total_leave_days', 'from_date', 'to_date', 'linked_lb_entry', 'from_balance'])
		for lv in lv_list:
			if not lv.linked_lb_entry:
				if range_from_date <= getdate(lv.from_date) <= range_to_date or range_from_date <= getdate(lv.to_date) <= range_to_date:
					deduct_credits_to = lv.leave_type
					deduct_to = frappe.db.get_value("Leave Type", lv.leave_type, "deduct_to")
					if deduct_to:
						deduct_credits_to = deduct_to

					lv.update({'deduct_credits_to': deduct_credits_to, 'employee_name': frappe.get_value("Employee", lv.employee, "full_name")})
					if lv.from_balance not in result:
						result[lv.from_balance] = lv

					if lv.from_balance not in inluded_from_balance:
						inluded_from_balance.append(lv.from_balance)

	return result, inluded_from_balance

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