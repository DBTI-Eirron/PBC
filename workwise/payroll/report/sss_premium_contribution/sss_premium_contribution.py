# -*- coding: utf-8 -*- 
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe, datetime
import codecs
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _, msgprint
from operator import itemgetter
import os

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
			row.append(format_precision(sss_amount, filters.value_precision))

		if total_sss > 0:
			final_employee += flt(gov_map[emp]["SSS"])
			final_employer += flt(gov_map[emp]["SSSE"])
			final_ec += flt(gov_map[emp]["SSSC"])
			final_total += total_sss
			row += [format_precision(total_sss, filters.value_precision)]
			
		data.append(row)
	data = sorted(data, key=itemgetter(1))
	final = ["<b>Total: </b>","", "", format_precision(final_employee, filters.value_precision), format_precision(final_employer, filters.value_precision), format_precision(final_ec, filters.value_precision), format_precision(final_total, filters.value_precision)]
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
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "SSSE",
			"label": _("Employer"),
			"fieldtype": "Data",
			"width":120
		},
		{
			"fieldname": "SSSC",
			"label": _("EC"),
			"fieldtype": "Data",
			"width":120
		},
		{
			"fieldname": "total_sss",
			"label": _("Total Contributions"),
			"fieldtype": "Data",
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
		{conditions}
		ORDER BY PR.employee_name""".format(conditions=get_conditions(filters.period_group)),{ 
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

def get_conditions(period_group):
	conditions = []
	if frappe.session.user != "Administrator":
		conditions.append(_("TE.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = '{0}' )").format(frappe.session.user))

	if period_group:
		conditions.append(_("TE.`period_group` = '{0}'").format(period_group))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

@frappe.whitelist()
def print_txt_file(company,from_date,to_date,period_group):
	employees = frappe.db.sql("""SELECT TE.name, TC.sss_id, TE.sss_no, TE.last_name, TE.first_name, TE.suffix, TE.middle_name, TE.date_hired, TE.date_retired, TE.date_resigned, TE.date_terminated, TE.position_title, TE.is_active
		FROM `tabEmployee` TE 
		INNER JOIN `tabCompany` TC ON TE.company = TC.name
		WHERE TE.company = %s
		{conditions}
		ORDER BY TE.last_name ASC""".format(conditions=get_conditions(period_group)),(company),as_dict=True)
	if not employees:
		frappe.throw(_("No Records Found"))

	pr_dict = {}
	for emp in employees:
		if emp.name not in pr_dict:
			pr_dict.setdefault(emp.name,frappe._dict({"comp":0.0}))

	pr_entries = frappe.db.sql("""SELECT PRE.amount, PR.employee 
		FROM `tabPayroll Register` PR
		INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.parent 
		WHERE PRE.pay_code IN ("SSS", "SSSE", "SSSC")
		AND PR.company = %(company)s 
		AND PR.posting_date BETWEEN %(from_date)s AND %(to_date)s
		{conditions}
		ORDER BY PR.employee_name""".format(conditions=get_conditions(period_group)),{ 
		"company": company,
		"from_date": from_date,
		"to_date": to_date
	}, as_dict=True)

	for pr in pr_entries:
		pr_dict[pr.employee]["comp"] += flt(pr.amount)

	f = open('site1.local/public/files/sss.txt','w+')
	for emp in employees:
		if emp.date_retired or emp.date_resigned or emp.date_terminated:
			is_term  = 1
			if emp.is_active == 0:
				term_date = emp.date_retired if emp.date_retired else emp.date_resigned if emp.date_resigned else emp.date_terminated
			else:
				term_date = emp.date_hired
		else:
			is_term = 0
			term_date = emp.date_hired
		middle_int = emp.middle_name[0] if emp.middle_name else "NULL"
		suffix = emp.suffix if emp.suffix else "NULL"
		sss_no = emp.sss_no.replace('-', '') if emp.sss_no else "NULL"
		#code gen
		code = ""
		if emp.is_active == 0:
			code += "1"
		else:
			code += "0"
		if is_term == 1:
			code += "1"
		else:
			code += "0"
		if pr_dict[emp.name]['comp'] > 0:
			code += "1"
		else:
			code += "0"
		#status	
		if code == "111":
			status = "2"
		elif getdate(from_date) <= getdate(term_date) <= getdate(to_date):
			status = "1"
		elif code == "000" or code == "010" or code == "100":
			status = "3"
		else:
			status = "N"

		# position
		if status == "1":
			position = emp.position_title
		else:
			position = "NULL"

		if pr_dict[emp.name]['comp'] > 0:
			term_date = getdate(term_date).strftime("%m%d%Y")
			sss_id = (emp.sss_id).replace('-', '')
			result = cstr(sss_id)+";000;"+cstr(sss_no)+";"+cstr(emp.last_name)+";"+cstr(emp.first_name)+";"+cstr(suffix)+";"+cstr(middle_int)+";"+cstr('{:.2f}'.format(pr_dict[emp.name]['comp']))+";"+cstr(status)+";"+cstr(term_date)+";"+cstr(position)+"\n"
			f.write(result.encode('latin1'))
	f.close()
	
	# frappe.local.response.filename = "test.txt"
	# with open("site1.local/public/files/sss.txt", "rb") as fileobj:
	# 	filedata = fileobj.read()
	# frappe.local.response.filecontent = filedata
	# frappe.local.response.type = "download"

	return  status