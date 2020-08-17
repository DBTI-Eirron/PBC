# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import date
from frappe import _
from frappe.utils import getdate, cstr, flt

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
			"width": 160
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
		
def get_data(filters):
	data = []
	data_entry = {}
	data_result = {}
	sorted_by = ['employee_name']
	location_included = [filters.location]

	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("To Date must be grater than From Date"))

	data.append({ "employee_name":"<b>Company: </b>"+filters.company })
	if filters.location:
		sorted_by.insert(0, 'location')
		data.append({ "employee_name":"<b>Location: </b>"+filters.location })
	data.append({})

	leave_balance = frappe.db.sql(""" SELECT LE.*, TE.full_name, TE.`location`
		FROM `tabLB Entry` LE INNER JOIN `tabEmployee` TE ON LE.`employee` = TE.`name` 
		LEFT JOIN `tabLocation` LOC ON TE.`location` = LOC.`name`
		WHERE TE.`company` = %(company)s {conditions} ORDER BY TE.full_name, LE.creation DESC """.format(conditions=get_conditions(filters)), filters, as_dict=1)

	#Init Data
	for lv in leave_balance:
		if lv.company == filters.company:
			doc_nam = cstr(lv.employee)+cstr(lv.leave_type)
			if lv.balance_type == 'Less':
				doc_nam = cstr(lv.employee)+cstr(lv.deduct_credits_to)

			if doc_nam not in data_entry:
				data_entry[doc_nam] = {
					"employee_name": cstr(lv.full_name),
					"location": lv.location,
					"valid_credits": 0,
					"add_entry": [],
					"less_entry": [],
				}

			if lv.balance_type == "Add":
				data_entry[doc_nam]['add_entry'].append({
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
	for dt in data_entry:
		for vl in data_entry[dt]['add_entry']:
			if ( ( vl['from_date'] <= getdate(filters.from_date) <= vl['to_date'] ) or ( vl['from_date'] <= getdate(filters.to_date) <= vl['to_date'] ) )\
			or ( ( getdate(filters.from_date) <= vl['from_date'] <= getdate(filters.to_date) ) or ( getdate(filters.from_date) <= vl['to_date'] <= getdate(filters.to_date) ) ):
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
			included_less = []
			for le in data_entry[dt]['less_entry']:
				if ( ( le['from_date'] <= getdate(filters.from_date) <= le['to_date'] ) or ( le['from_date'] <= getdate(filters.to_date) <= le['to_date'] ) )\
				or ( ( getdate(filters.from_date) <= le['from_date'] <= getdate(filters.to_date) ) or ( getdate(filters.from_date) <= le['to_date'] <= getdate(filters.to_date) ) ):
					if (vl['credits'] > 0) and (not le['included']):
						if ( vl['from_date'] <= le['from_date'] <= vl['to_date'] ) or ( vl['from_date'] <= le['to_date'] <= vl['to_date'] ):
							to_less += le['credits']
				 			le['included'] = 1
						included_less.append(le)
			vl['credits'] -= to_less
			if ( ( vl['from_date'] <= getdate(filters.from_date) <= vl['to_date'] ) or ( vl['from_date'] <= getdate(filters.to_date) <= vl['to_date'] ) )\
			or ( ( getdate(filters.from_date) <= vl['from_date'] <= getdate(filters.to_date) ) or ( getdate(filters.from_date) <= vl['to_date'] <= getdate(filters.to_date) ) ):
				data_result[dt]['valid_credits'] += vl['credits']
				
			for inc in included_less:
				if dt in data_result:
					data_result[dt]['entry'].append(inc)

	#Generate Data
	for dat in sorted( data_result.items(), key=lambda k: [k[1][s] for s in sorted_by] ):
		if (filters.location) and (dat[1]['location'] not in location_included):
			data.append({ "employee_name":"<b>Location: </b>"+dat[1]['location'] })
			location_included.append(dat[1]['location'])

		for lv_typ in sorted(dat[1]["entry"], key=lambda k: k['creation']):
			row = {
				"employee_name": dat[1]["employee_name"],
				"leave_type": lv_typ["leave_type"],
				"type": lv_typ["type"],
				"from_date": lv_typ["from_date"],
				"to_date": lv_typ["to_date"],
				"credits": lv_typ["credits"],
				"used_in": lv_typ["application"],
				"deduct_to": lv_typ["deduct_credits_to"],
			}
			data.append(row)
		
		if dat[1]["entry"]:
			data.append({
				"employee_name": "",
				"leave_type": "<b>Remaining Balance",
				"credits": dat[1]["valid_credits"] if dat[1]["valid_credits"] > 0 else 0,
				"type": "</b>",
				"from_date": "",
				"to_date": "",
				"used_in": "",
				"deduct_to": "",
				"full_name": dat[1]["employee_name"],
			})
			data.append({})

	return data

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("LE.`employee`=%(employee)s")

	if filters.location:
		conditions.append("TE.`location`=%(location)s")

	if filters.get("leave_type"):
		conditions.append("LE.`leave_type`=%(leave_type)s")

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 