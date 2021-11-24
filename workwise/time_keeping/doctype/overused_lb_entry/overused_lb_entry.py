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
def get_employees_with_overused_credits():
	result = []
	data_entry = {}
	data_result = {}
	from_date = nowdate()
	to_date = nowdate()
	included_lawle = []
	leave_applications_without_less_lbentry = get_leave_applications_without_less_lbentry(from_date, to_date)
	leave_balance = frappe.db.sql(""" SELECT LE.*, TE.full_name
	FROM `tabLB Entry` LE INNER JOIN `tabEmployee` TE ON LE.`employee` = TE.`name` 
	ORDER BY TE.full_name, LE.creation DESC """, as_dict=1)

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
			doc.employee = i.get("employee")
			doc.employee_name = frappe.db.get_value("Employee", i.get("employee"), "full_name")
			doc.company = frappe.db.get_value("Employee", i.get("employee"), "company")
			doc.status = "Pending"
			doc.overused_credits = abs(i.get("credits"))
			doc.leave_type = i.get("leave_type")
			doc.deducted_credits = 0
			doc.remaining_overused_credits = abs(i.get("credits"))
			doc.flags.ignore_permissions = True
			doc.insert()

def get_leave_applications_without_less_lbentry(from_date, to_date):
	result = {}
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

					if deduct_credits_to not in result[lv.employee]:
						result[lv.employee][deduct_credits_to] = 0

					result[lv.employee][deduct_credits_to] += flt(lv.total_leave_days, 2)

	return result