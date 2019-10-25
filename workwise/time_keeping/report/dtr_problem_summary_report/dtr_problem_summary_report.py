# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	data = get_data(filters)
	columns = get_columns(filters)
	return columns, data

def get_data(filters):
	data = []
	from_date,to_date = frappe.get_value('Payroll Period',filters.payroll_period,['attendance_from','attendance_to'])
	employees = get_employee(filters)
	for emp in employees:
		result = frappe.db.sql("""SELECT DPA.`employee_name`,DPA.`name`,DPA.`target_date`,DPT.`type`,DPT.`current`,DPT.`request`
		FROM `tabDTR Problem Application` DPA INNER JOIN `tabDTR Problem Table` DPT ON DPA.`name` = DPT.`parent` WHERE DPA.docstatus = 1 AND DPA.employee = %s AND DPA.target_Date BETWEEN %s AND %s""",(emp.name,from_date,to_date),as_dict=True)
		for res in result:
			data.append({'employee_name':res.employee_name,'application':res.name,'date':res.target_date,'type':res.type,'current':res.current,'requested':res.request})
	return data

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 200
		},{
			"fieldname": "application",
			"label": _("Application"),
			"fieldtype": "Link",
			"options":"DTR Problem Application",
			"width": 150
		},{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Data",
			"width": 150
		},{
			"fieldname": "type",
			"label": _("Type"),
			"fieldtype": "Data",
			"width": 150
		},{
			"fieldname": "current",
			"label": _("Current"),
			"fieldtype": "Data",
			"width": 150
		},{
			"fieldname": "requested",
			"label": _("Requested"),
			"fieldtype": "Data",
			"width": 150
		},
	]

	return columns

def get_employee(filters):
	query = "SELECT TE.`name`, TE.`full_name` FROM `tabEmployee` TE LEFT JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name` WHERE TE.docstatus = 0"
	if filters.employee:
		query = query + " AND TE.`name` = '"+filters.employee+"'"
	else:
		if filters.company:
			query = query + " AND TE.company = '"+filters.company+"'"
		if filters.location:
			query = query + " AND TE.location = '"+filters.location+"'"
		if filters.department:
			lft, rgt = frappe.db.get_value("Department", filters.department, ["lft", "rgt"])
			query = query + " AND ( DEPT.`lft` BETWEEN '{0}' AND '{1}' )".format(lft, rgt)
		if filters.position_title:
			query = query + " AND TE.position_title = '"+filters.position_title+"'"
	employees = frappe.db.sql(query,as_dict=True)

	return employees