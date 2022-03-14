# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	employee_list = get_employees(filters)
	
	if not employee_list:
		frappe.throw(_("No record found"))
		return columns, employee_list

	data = []

	for emp in employee_list:
		row = {
			"department": emp.department,
			"employee_name": emp.employee_name,
			"training": emp.training,
			"provider": emp.provider,
			"contact": "",
			"lrf_date": "",
			"reg_date": emp.target_date,
			"amount": emp.budget,
			"paid": "",
			"savings": "",
			"date_attended": "",
			"status": emp.status,
		}

		data.append(row)

	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "department",
			"label": _("SUBSIDIARY/DEPARTMENT"),
			"fieldtype": "Data",
			"width": 160
		},
		{
			"fieldname": "employee_name",
			"label": _("EMPLOYEE NAME"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "training",
			"label": _("TITLE OF SEMINAR/TRAINING"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "provider",
			"label": _("TRAINING PROVIDER"),
			"fieldtype": "Data",
			"width": 180
		},
		#{
		#	"fieldname": "contact",
		#	"label": _("CONTACT NUMBER/EMAIL ADD"),
		#	"fieldtype": "Data",
		#	"width": 180
		#},
		#{
		#	"fieldname": "lrf_date",
		#	"label": _("DATE LRF RECEIVED"),
		#	"fieldtype": "Data",
		#	"width": 180
		#},
		{
			"fieldname": "reg_date",
			"label": _("DATE REGISTERED"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "amount",
			"label": _("ACTUAL AMOUNT"),
			"fieldtype": "Data",
			"width": 180
		},
		#{
		#	"fieldname": "paid",
		#	"label": _("AMOUNT PAID"),
		#	"fieldtype": "Data",
		#	"width": 180
		#},
		#{
		#	"fieldname": "savings",
		#	"label": _("SAVINGS"),
		#	"fieldtype": "Data",
		#	"width": 180
		#},
		#{
		#	"fieldname": "date_attended",
		#	"label": _("DATE ATTENDED"),
		#	"fieldtype": "Data",
		#	"width": 180
		#},
		{
			"fieldname": "status",
			"label": _("STATUS"),
			"fieldtype": "Data",
			"width": 180
		},
	]

	return columns

def get_employees(filters):
	employees = frappe.db.sql(""" SELECT DISTINCT
		WN.employee_name,
		WN.training,
		WN.provider,
		WN.`target_date`,
		WN.budget,
		WN.status,
		WL.department
		FROM
		`tabWLD Needs Table` WN INNER JOIN `tabEmployee` TE ON WN.`employee`=TE.`name` INNER JOIN `tabWLD Needs` WL ON WN.`parent`=WL.`name`
		WHERE
		WL.`company` = %(company)s {conditions} AND WN.docstatus = 1 """.format(conditions=get_employee_conditions(filters)),{ 
		"company": filters.company,
		"department": filters.department,
	}, as_dict=True)

	return employees

def get_employee_conditions(filters):
	conditions = []
	if filters.department:
		conditions.append("WL.department=%(department)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""