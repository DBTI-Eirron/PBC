# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import date
from frappe import _
from frappe.utils import getdate, cstr

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "credits",
			"label": _("Credits"),
			"fieldtype": "Float",
			"width": 130
		},
		{
			"fieldname": "used_credits",
			"label": _("Used Credits"),
			"fieldtype": "Float",
			"width": 130
		},
		{
			"fieldname": "balance",
			"label": _("Credit Balance"),
			"fieldtype": "Float",
			"width": 130
		},
	]

	return columns

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_balances(emp_map, filters, from_date, to_date):
	result = {}

	if filters.valid_from:
		from_date = filters.valid_from
	if filters.valid_to:
		from_date = filters.valid_to
	if getdate(from_date) > getdate(to_date):
		frappe.throw(_("Valid To must be grater than Valid From"))

	balances = frappe.db.sql(""" SELECT LE.* FROM `tabLB Entry` LE WHERE `company` = %s """,(filters.company), as_dict=True)
	lv_bal = get_lb_entry_balance(balances, from_date, to_date)

	for d in lv_bal:
		if d['employee'] in emp_map:
			emp_map[d['employee']].balances.append({
				"employee": d['employee'],
				"leave_type": d['leave_type'],
				"valid_credits": d['balance'],
				"credits": d['credits'],
				"used_credits": d['used'],
			})

def get_company_list(filters):
	result = {}

	filt = {}
	if filters.company:
		filt = {'name': filters.company}

	company = frappe.db.get_list('Company', filters=filt, fields=['name'])
	for com in company:
		result[com['name']] = {}

	return result

def get_leave_types():
	leave_types = frappe.db.sql(""" SELECT `name`, leave_code, deduct_to FROM `tabLeave Type` 
		ORDER BY leave_code ASC """, as_dict=True)

	return leave_types
					
def get_data(filters):
	data = []
	data_entry = {}
	company = {}
	period_group_list = []
	location_list = []
	from_date, to_date = frappe.db.get_value("Payroll Year", filters.year, ["from_date", "to_date"])
	emp_map = init_employee_map(filters, data_entry)
	leave_types = get_leave_types()
	get_balances(emp_map, filters, from_date, to_date)

	for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
		sub_data = []
		entry = {
			"employee": _("<b>"+emp_dict.employee_name+"</b>"),
			"period_group": emp_dict.period_group,
			"location": emp_dict.location
		}	
		sub_data.append(entry)

		for lt in leave_types:
			sub_entry = {
				"employee": lt.name,
				"credits": 0.0,
				"used_credits": 0.0,
				"balance": 0.0,
			}

			if lt.name not in company:
				company.update({
					lt.name: {
						"credits": 0.0,
						"used_credits": 0.0,
						"balance": 0.0,
					}
				})

			for bal in emp_dict.get('balances'):
				if lt.name == bal['leave_type']:
					sub_entry['credits'] += bal['credits']
					sub_entry['used_credits'] += bal['used_credits']
					sub_entry['balance'] += bal['valid_credits']

					company[lt.name]['credits'] += bal['credits']
					company[lt.name]['used_credits'] += bal['used_credits']
					company[lt.name]['balance'] += bal['valid_credits']

			sub_data.append(sub_entry)
		data_entry[emp_dict.period_group][emp_dict.location].append(sub_data)
	
	if not filters.employee:
		data += [{"employee":"<b>Summary</b>"}]
		for com in sorted(company.keys()):
			company_summary = {
				"employee": com,
				"credits": company[com]['credits'],
				"used_credits": company[com]['used_credits'],
				"balance": company[com]['balance'],
			}
			data.append(company_summary)
		data.append({})
	
	for per in sorted(data_entry.keys()):
		data += [{"employee":"<b>"+str(per)+"</b>"}]
		for loc in sorted(data_entry[per].keys()):
			data += [{"employee":"<b>"+str(loc)+"</b>"}]
			for ent in data_entry[per][loc]:
				if ent:
					data += ent
					data.append({})
					
	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)
	return result

def init_employee_map(filters, data_entry):
	employees = frappe.db.sql("""SELECT TE.`name`, TE.`full_name`, TE.`period_group`, TE.`location`, TE.`company` FROM `tabEmployee` TE
		LEFT JOIN `tabLocation` LOC ON TE.`location` = LOC.`name`
		WHERE TE.company = %(company)s {conditions}""".format(conditions=get_conditions(filters)), filters, as_dict=1)

	emp_map = frappe._dict()
	for emp in employees:
		emp_map.setdefault(emp.name, frappe._dict({
				"employee_name": emp.full_name,
				"balances": [],
				"period_group": emp.period_group,
				"location": emp.location,
				"company": emp.company,
			})
		)

		if not emp.period_group in data_entry:
			data_entry.update( { emp.period_group: {} } )
		if not emp.location in data_entry[emp.period_group]:
			data_entry[emp.period_group].update({ emp.location: [] })

	return emp_map

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("TE.`name`=%(employee)s")

	if filters.get("period_group"):
		conditions.append("TE.`period_group`=%(period_group)s")

	if filters.location:
		conditions.append("TE.`location`=%(location)s")

	if filters.company:
		conditions.append("TE.`company`=%(company)s")

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 


def get_lb_entry_balance(balance_list, from_date, to_date):
	result = []
	data = {}

	for li in balance_list:
		emp = cstr(li['employee'])
		lvtype = cstr(li['leave_type'])
		if li.balance_type == 'Less':
			lvtype = cstr(li['deduct_credits_to'])

		if emp not in data:
			data[emp] = {}
		if lvtype not in data[emp]:
			data[emp][lvtype] = {
				'add_entry': [],
				'less_entry': [],
				'balance': 0,
				'credits': 0,
				'used': 0,
			}

		if li.balance_type == 'Add':
			data[emp][lvtype]['add_entry'].append({
				"credits": li.credits,
				"from_date": getdate(li.from_date),
				"to_date": getdate(li.to_date),
			})

		if li.balance_type == 'Less':
			data[emp][lvtype]['less_entry'].append({
				"included": 0,
				"credits": li.credits,
				"from_date": getdate(li.from_date),
				"to_date": getdate(li.to_date),
			})

	for d in data:
		for l in data[d]:
			for ad in data[d][l]['add_entry']:
				to_less = 0
				ad_from = ad['from_date']
				ad_to = ad['to_date']
				ad_cred = ad['credits']
				if (( ad_from <= getdate(from_date) <= ad_to ) or ( ad_from <= getdate(to_date) <= ad_to )) \
				or (( getdate(from_date) <= ad_from <= getdate(to_date) ) or ( getdate(from_date) <= ad_to <= getdate(to_date) )):
					data[d][l]['credits'] += ad_cred
					for le in data[d][l]['less_entry']:
						le_from = le['from_date']
						le_to = le['to_date']
						le_included = le['included']
						le_cred = le['credits']

						if ad_cred > 0 and not le_included:
							if ( ad_from <= le_from <= ad_to ) or ( ad_from <= le_to <= ad_to )\
							or ( le_from <= ad_from <= le_to ) or ( le_from <= ad_to <= le_to ):
								to_less += le_cred
								le['included'] = 1
								data[d][l]['used'] += le_cred
					ad['credits'] -= to_less
					data[d][l]['balance'] += ad['credits']

			result.append({
				'employee': d,
				'leave_type': l,
				'balance': abs(data[d][l]['credits'] - data[d][l]['used']),
				'credits': data[d][l]['credits'],
				'used': data[d][l]['used'],
			})

	return result