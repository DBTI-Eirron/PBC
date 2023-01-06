# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import (flt, getdate, get_first_day, get_last_day, date_diff, add_months, add_days, formatdate, cint)
from workwise.payroll.payroll_utils import get_rates
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	results = get_result(filters)
	return columns, results

def get_columns(filters):
	period_list = get_period_list(filters)
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 200
		},
	]

	for period in period_list:
		columns.append({
			"fieldname": period.key,
			"label": period.label,
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150
		})

	columns += [
		{
			"fieldname": "total_bonus",
			"label": _("Total Amount"),
			"fieldtype": "Currency",
			"width": 120
		},
	]

	return columns

def get_period_list(filters):
	from_year, to_year = frappe.db.get_value("Payroll Year", filters.payroll_year, ["from_date", "to_date"])

	year_start_date = getdate(from_year)
	year_end_date = getdate(to_year)

	start_date = from_year
	months = get_months(year_start_date , year_end_date)
	period_list = []

	for i in xrange(months):
		period = frappe._dict({
			"from_date": start_date
		})

		to_date = add_months(start_date, 1)
		start_date = to_date

		if to_date == get_first_day(to_date):
			# if to_date is the first day, get the last day of previous month
			to_date = add_days(to_date, -1)

		if to_date <= year_end_date:
			# the normal case
			period.to_date = to_date
		else:
			# if a fiscal year ends before a 12 month period
			period.to_date = year_end_date

		period_list.append(period)

		if period.to_date == year_end_date:
			break

	# common processing
	for opts in period_list:
		key = opts["to_date"].strftime("%b_%Y").lower()
		label = formatdate(opts["to_date"], "MMM YYYY")

		opts.update({
			"key": key.replace(" ", "_").replace("-", "_"),
			"label": label,
		})

	return period_list

def get_months(start_date, end_date):
	diff = (12 * end_date.year + end_date.month) - (12 * start_date.year + start_date.month)
	return diff + 1

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)
	return result

def get_data(filters):
	data = []
	from_year, to_year = frappe.db.get_value("Payroll Year", filters.payroll_year, ["from_date", "to_date"])
	_map = init_map(filters)
	get_registers(_map, filters, from_year, to_year)
	period_list = get_period_list(filters)
	for e, edict in sorted(_map.items(), key=lambda x: x[1]['employee_name']):
		rates = get_rates(edict['employee_details'])
		total_bonus = 0

		for period in period_list:
			edict[period.key] = 0.0
		
		for d in edict.get('registers'):
			for period in period_list:
				if getdate(period.from_date) <= getdate(d.posting_date) <= getdate(period.to_date):
					edict[period.key] += d.amount

		if filters.assume_last_month:
			edict[period_list[-1].key] = rates.get('monthly_rate')

		for period in period_list:
			total_bonus += edict[period.key]

		edict['total_bonus'] = total_bonus / 12
		edict['registers'] = ""
		data.append(edict)
				
	return data

def init_map(filters):
	init_data = frappe.db.sql("""SELECT `name`, full_name, employee_id, no_hours, total_yr_days, rate_type, rate FROM `tabEmployee` PR
		WHERE company = %(company)s AND is_active = 1 {conditions} """.format(conditions=get_conditions_emp(filters)), filters, as_dict=1)
	get_period_list(filters)

	_map = frappe._dict()
	for d in init_data:
		_map.setdefault(d.name, frappe._dict({
				"employee": d.name,
				"employee_name": d.full_name,
				"employee_details": d,
				"registers": [],
				"total_bonus": 0.0
			})
		)

	return _map

def get_registers(_map, filters, from_year, to_year):
	registers = frappe.db.sql(""" SELECT PR.period, PRE.`name`, PR.employee, PR.posting_date, PRE.pay_code, PRE.amount
		FROM `tabPayroll Register Entries` PRE INNER JOIN `tabPayroll Register` PR ON PRE.`parent`=PR.`name`
		WHERE PRE.`pay_code` = 'BS' AND company = %(company)s AND PR.posting_date >= %(from_year)s AND PR.posting_date <= %(to_year)s """,
	{ 
		"company": filters.company,
		"from_year": from_year,
		"to_year": to_year,
	}, as_dict=True)

	pay_period_list = get_payroll_period_list(filters)
	for d in registers:
		if d.period in pay_period_list:
			if d.employee in _map:
				_map[d.employee].registers.append(d)


def get_conditions_emp(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_payroll_period_list(filters):
	pay_period_list = []
	pay_periods = frappe.db.sql(""" SELECT `name` FROM `tabPayroll Period` WHERE company = %(company)s AND payroll_year = %(payroll_year)s """,{ 
		"company": filters.company,
		"payroll_year": filters.payroll_year,
	}, as_dict=True)

	for d in pay_periods:
		pay_period_list.append(d.name)

	return pay_period_list