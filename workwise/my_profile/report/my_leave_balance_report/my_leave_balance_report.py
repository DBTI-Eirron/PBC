# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, cstr

def execute(filters=None):
	columns = get_columns(filters)
	results = get_data(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "leave_type",
			"label": _("Leave Type"),
			"fieldtype": "Data",
			"width": 250,
		},
		{
			"fieldname": "credits",
			"label": _("Credits"),
			"fieldtype": "Float",
			"width": 180
		},
		{
			"fieldname": "used_credits",
			"label": _("Used Credits"),
			"fieldtype": "Float",
			"width": 180
		},
		{
			"fieldname": "credit_balance",
			"label": _("Credit Balance"),
			"fieldtype": "Float",
			"width": 180
		},
	]

	return columns

def get_data(filters):
	data = []
	data_entry = {}
	leave_types = get_leave_types()
	lb_entries = get_balances(filters)
	from_date = filters.from_date
	to_date = filters.to_date
	
	for lt in leave_types:
		sub_entry = {
			"leave_type": lt,
			"credits": 0.0,
			"used_credits": 0.0,
			"credit_balance": 0.0,
		}
		if lb_entries and lt in lb_entries:
			for ad in lb_entries[lt]['add']:
				to_less = 0
				ad_from = ad['from_date']
				ad_to = ad['to_date']
				ad_cred = ad['credits']
				if (( ad_from <= getdate(from_date) <= ad_to ) or ( ad_from <= getdate(to_date) <= ad_to )) \
				or (( getdate(from_date) <= ad_from <= getdate(to_date) ) or ( getdate(from_date) <= ad_to <= getdate(to_date) )):
					sub_entry['credits'] += ad_cred
					for le in lb_entries[lt]['less']:
						le_from = le['from_date']
						le_to = le['to_date']
						le_included = le['included']
						le_cred = le['credits']

						if ad_cred > 0 and not le_included:
							if ( ad_from <= le_from <= ad_to ) or ( ad_from <= le_to <= ad_to ):
								to_less += le_cred
								le['included'] = 1
								sub_entry['used_credits'] += le_cred
						ad['credits'] -= to_less
					if (( ad_from <= getdate(from_date) <= ad_to ) or ( ad_from <= getdate(to_date) <= ad_to )) \
					or (( getdate(from_date) <= ad_from <= getdate(to_date) ) or ( getdate(from_date) <= ad_to <= getdate(to_date) )):
						sub_entry['credit_balance'] += ad['credits']
		data.append(sub_entry)

	return data

def get_leave_types():
	result = []
	leave_types = frappe.db.sql(""" SELECT `name`, leave_code, deduct_to FROM `tabLeave Type` 
		ORDER BY leave_code ASC """, as_dict=True)
	for d in leave_types:
		result.append(d.name)

	return result

def get_balances(filters):
	result = {}
	emp = frappe.db.sql("""SELECT `name`, `company` FROM `tabEmployee` WHERE `user_id` = %s LIMIT 1""",( frappe.session.user ), as_dict=1)
	if emp:
		balances = frappe.db.sql(""" SELECT * FROM `tabLB Entry` WHERE `company` = %s AND employee = %s """,(emp[0].company, emp[0].name), as_dict=1)

		for d in balances:
			lv = d.leave_type
			if d.deduct_credits_to:
				lv = d.deduct_credits_to

			if lv not in result:
				result[lv] = {
					'add': [],
					'less': [],
				}

			if d.balance_type == 'Add':
				result[lv]['add'].append(d)
			if d.balance_type == 'Less':
				d["included"] = 0
				result[lv]['less'].append(d)

	return result