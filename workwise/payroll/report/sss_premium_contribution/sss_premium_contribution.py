# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_decimal_by_2, format_decimal_by_2_align_right, format_decimal_by_2_align_right_negative
from frappe import _, msgprint
from operator import itemgetter

def execute(filters=None):
	columns = get_columns()

	transaction_type = ['SSS', 'SSSE', 'SSSC']
	employee_list, gov_map = get_employees(filters,transaction_type)
	

	final_employee, final_employer, final_ec, final_total = 0, 0, 0, 0

	data = []
	for emp in gov_map:
		row = [gov_map[emp]['employee'], gov_map[emp]['full_name'], gov_map[emp]['sss_no']]

		total_sss = 0
		for trans in transaction_type:
			sss_amount = gov_map[emp][trans]
			total_sss += sss_amount
			row.append(format_decimal_by_2(sss_amount))

		if total_sss > 0:
			final_employee += flt(gov_map[emp]["SSS"])
			final_employer += flt(gov_map[emp]["SSSE"])
			final_ec += flt(gov_map[emp]["SSSC"])
			final_total += total_sss
			row += [format_decimal_by_2(total_sss)]
			
		data.append(row)
	data = sorted(data, key=itemgetter(1))
	final = ["<b>Total: </b>","", "", format_decimal_by_2(final_employee), format_decimal_by_2(final_employer), format_decimal_by_2(final_ec), format_decimal_by_2(final_total)]
	data.append(final)
	return columns, data

def get_columns():
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 220
		},
		{
			"fieldname": "sss_no",
			"label": _("SSS Number"),
			"fieldtype": "Data",
			"width": 160
		},
		{
			"fieldname": "SSS",
			"label": _("Employee"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "SSSE",
			"label": _("Employer"),
			"fieldtype": "Float",
			"width":120
		},
		{
			"fieldname": "SSSC",
			"label": _("EC"),
			"fieldtype": "Float",
			"width":120
		},
		{
			"fieldname": "total_sss",
			"label": _("Total Contributions"),
			"fieldtype": "Float",
			"width": 100
		},
	]

	return columns

def get_employees(filters,transaction_type):
	employees = frappe.db.sql("""SELECT PRE.pay_code, PRE.amount, PR.posting_date, PR.employee as `name`, PR.employee_name as full_name, TE.sss_no
		FROM `tabPayroll Register Entries` PRE
		INNER JOIN `tabPayroll Register` PR ON PRE.`parent` = PR.`name`
		INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		WHERE PRE.pay_code IN ('"""+"','".join(str(e) for e in transaction_type)+"""') 
		AND PR.company = %(company)s 
		AND PR.posting_date BETWEEN %(from_date)s AND %(to_date)s
		AND TE.is_active = 1
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
			type_list.update({"full_name":d.full_name,"sss_no":d.sss_no,"employee":d.name})
			gov_map.setdefault(d.name, frappe._dict(type_list))
		gov_map[d.name][d.pay_code] += flt(d.amount)
	return employees, gov_map

def get_conditions(filters):
	conditions = []
	if frappe.session.user != "Administrator":
		conditions.append(_("TE.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = '{0}' )").format(frappe.session.user))

	if filters.period_group:
		conditions.append(_("TE.`period_group` = '{0}'").format(filters.period_group))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 
