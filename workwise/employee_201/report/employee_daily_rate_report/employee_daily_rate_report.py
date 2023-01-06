# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr
from frappe import _
from workwise.payroll.payroll_utils import get_rates

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_data(filters):
	data = []
	worked_on_march_14_2020_list = []
	worked_on_march_15_2020_list = []
	worked_on_march_16_2020_list = []

	attreg_list = frappe.db.sql("""SELECT `name`, `employee`, `target_date`,`is_absent` FROM `tabAttendance Register` WHERE `target_date` >= '2020-03-14' AND `target_date` <= '2020-03-16' """, as_dict=1)
	for att in attreg_list:
		if getdate(att.target_date) == getdate('2020-03-14') and not att.is_absent:
			worked_on_march_14_2020_list.append(att.employee)

		if getdate(att.target_date) == getdate('2020-03-15') and not att.is_absent:
			worked_on_march_15_2020_list.append(att.employee)

		if getdate(att.target_date) == getdate('2020-03-16') and not att.is_absent:
			worked_on_march_16_2020_list.append(att.employee)

	emp_list = get_employees(filters)
	for emp in emp_list:
		worked_on_march_14_2020 = 0
		worked_on_march_15_2020 = 0
		worked_on_march_16_2020 = 0

		if emp.name in worked_on_march_14_2020_list:
			worked_on_march_14_2020 = 1

		if emp.name in worked_on_march_15_2020_list:
			worked_on_march_15_2020 = 1

		if emp.name in worked_on_march_16_2020_list:
			worked_on_march_16_2020 = 1

		rates = get_rates(emp)
		row = {
			'employee': emp.name,
			'employee_name': emp.full_name,
			'rate_type': emp.rate_type,
			'rate': emp.rate,
			'daily_rate': rates["daily_rate"],
			'worked_on_march_14_2020': worked_on_march_14_2020,
			'worked_on_march_15_2020': worked_on_march_15_2020,
			'worked_on_march_16_2020': worked_on_march_16_2020,
		}
		data.append(row)

	return data

def get_employees(filters):
	conditions = ""
	if frappe.session.user != "Administrator":
		conditions = ("WHERE allow_user = '{0}' ").format(frappe.session.user)

	employees = frappe.db.sql("""SELECT `name`, `full_name`, `rate_type`, `rate`, `total_yr_days`, `no_hours` FROM `tabEmployee`
		WHERE sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` {conditions})
		AND company = %(company)s AND is_active = 1 ORDER BY `full_name` """.format( conditions=conditions ),{ 
			"company": filters.company
		}, as_dict=True)

	return employees

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options":"Employee",
			"width": 150
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "rate_type",
			"label": _("Rate Type"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "rate",
			"label": _("Rate "),
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "daily_rate",
			"label": _("Daily Rate"),
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "worked_on_march_14_2020",
			"label": _("Worked on March 14 2020"),
			"fieldtype": "Check",
			"width": 200
		},
		{
			"fieldname": "worked_on_march_15_2020",
			"label": _("Worked on March 15 2020"),
			"fieldtype": "Check",
			"width": 200
		},
		{
			"fieldname": "worked_on_march_16_2020",
			"label": _("Worked on March 16 2020"),
			"fieldtype": "Check",
			"width": 200
		},
	]
	return columns