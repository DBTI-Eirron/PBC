# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _, msgprint

def execute(filters=None):
	if not filters: filters = frappe._dict({})
	validate_filters(filters)

	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_columns(filters):
	sep_name = frappe.db.get_single_value('Payroll Settings', 'separate_name')
	columns = [
		{
		"fieldname": "phic_no",
		"label": _("PHIC Number"),
		"fieldtype": "Data",
		"width": 170
		},{
		"fieldname": "monthly_rate",
		"label": _("Monthly Rate"),
		"fieldtype": "Data",
		"width": 100
		},
	]
	if sep_name:
		columns += [
			{
			"fieldname": "last_name",
			"label": _("Last Name"),
			"fieldtype": "Data",
			"width": 120
			},{
			"fieldname": "first_name",
			"label": _("First Name"),
			"fieldtype": "Data",
			"width": 120
			},{
			"fieldname": "middle_name",
			"label": _("Middle Name"),
			"fieldtype": "Data",
			"width": 120
			},
		]
	else:
		columns += [
			{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 120
			},
		]
	columns += [
		{
		"fieldname": "employee_status",
		"label": _("Employee Status"),
		"fieldtype": "Data",
		"width": 120
		},{
		"fieldname": "date_hired",
		"label": _("Date of Hired"),
		"fieldtype": "Data",
		"width": 120
		},{
		"fieldname": "birth_day",
		"label": _("Date of Birth"),
		"fieldtype": "Data",
		"width": 100
		},{
		"fieldname": "employee",
		"label": _("Employee"),
		"fieldtype": "Data",
		"width": 100
		},{
		"fieldname": "employer",
		"label": _("Employer"),
		"fieldtype": "Data",
		"width": 100
		},
	]

	return columns

def get_data(filters):
	#Initialize
	data = []
	transaction_type = ['PHIC','PHICE']
	sep_name = frappe.db.get_single_value('Payroll Settings', 'separate_name')
	gov_map = get_employees(filters,transaction_type)
	if not gov_map:
		frappe.msgprint("No Records Found");
	else:
		total_phic, total_phice = 0, 0
		for emp in sorted(gov_map.items(), key = lambda k:k[1]['full_name']):
			total_phic += gov_map[emp[0]]['PHIC']
			total_phice += gov_map[emp[0]]['PHICE']
			if sep_name:
				row = {
					"phic_no": gov_map[emp[0]]['phic_no'],
					"monthly_rate": gov_map[emp[0]]['rate'],
					"last_name": gov_map[emp[0]]['last_name'],
					"first_name": gov_map[emp[0]]['first_name'],
					"middle_name": gov_map[emp[0]]['middle_name'],
					"employee_status": "Active" if gov_map[emp[0]]['status'] == 1 else "Inactive",
					"date_hired": datetime.datetime.strftime(getdate(gov_map[emp[0]]['date_hired']), "%m/%d/%Y"),
					"birth_day": datetime.datetime.strftime(getdate(gov_map[emp[0]]['birthday']), "%m/%d/%Y"),
					"employee": format_precision(gov_map[emp[0]]['PHIC'], filters.value_precision),
					"employer": format_precision(gov_map[emp[0]]['PHICE'], filters.value_precision),
				}
			else:
				row = {
					"phic_no": gov_map[emp[0]]['phic_no'],
					"monthly_rate": gov_map[emp[0]]['rate'],
					"employee_name": gov_map[emp[0]]['full_name'],
					"employee_status": "Active" if gov_map[emp[0]]['status'] == 1 else "Inactive",
					"date_hired": datetime.datetime.strftime(getdate(gov_map[emp[0]]['date_hired']), "%m/%d/%Y"),
					"birth_day": datetime.datetime.strftime(getdate(gov_map[emp[0]]['birthday']), "%m/%d/%Y"),
					"employee": format_precision(gov_map[emp[0]]['PHIC'], filters.value_precision),
					"employer": format_precision(gov_map[emp[0]]['PHICE'], filters.value_precision),
				}
			data.append(row)
		#Totals
		if sep_name:
			data.append({
				"phic_no": "",
				"monthly_rate": "",
				"last_name": "",
				"first_name": "",
				"middle_name": "",
				"employee_status": "",
				"date_hired": "",
				"birth_day": "",
				"employee": format_precision(total_phic, filters.value_precision),
				"employer": format_precision(total_phice, filters.value_precision),
			})
		else:
			data.append({
				"phic_no": "",
				"monthly_rate": "",
				"employee_name": "",
				"employee_status": "",
				"date_hired": "",
				"birth_day": "",
				"employee": format_precision(total_phic, filters.value_precision),
				"employer": format_precision(total_phice, filters.value_precision),
			})

	return data


def get_employees(filters,transaction_type):
	employees = frappe.db.sql("""SELECT PRE.pay_code, PRE.amount, PR.posting_date, PR.employee as `name`, PR.employee_name as full_name, TE.phic_no, TE.first_name, TE.last_name, TE.middle_name, TE.tin, TE.birthday,TE.rate,TE.is_active,TE.date_hired
		FROM `tabPayroll Register Entries` PRE
		INNER JOIN `tabPayroll Register` PR ON PRE.`parent` = PR.`name`
		INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		WHERE PRE.pay_code IN ('"""+"','".join(str(e) for e in transaction_type)+"""') 
		AND PR.company = %(company)s 
		AND PR.posting_date BETWEEN %(from_date)s AND %(to_date)s
		{conditions}
		ORDER BY PR.employee_name""".format(conditions=get_conditions(filters)),{ 
		"company": filters.company,
		"from_date": filters.from_date,
		"to_date": filters.to_date
	}, as_dict=True)
	if not employees:
		frappe.throw(_("No Records Found"))

	type_list = {}
	for t in transaction_type:
		type_list.update({t:0.0})

	gov_map = {}
	for d in employees:
		if d.name not in gov_map:
			type_list.update({"full_name":d.full_name,"phic_no":d.phic_no,"employee":d.name,"first_name":d.first_name,"last_name":d.last_name,"middle_name":d.middle_name,"tin":d.tin,"birthday":d.birthday,"rate":d.rate,"status":d.is_active,"date_hired":d.date_hired})
			gov_map.setdefault(d.name, frappe._dict(type_list))
		gov_map[d.name][d.pay_code] += flt(d.amount)
	return gov_map

def get_conditions(filters):
	conditions = []
	if frappe.session.user != "Administrator":
		conditions.append(_("TE.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

	if filters.period_group:
		conditions.append(_("TE.`period_group` = '{0}'").format(filters.period_group))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))