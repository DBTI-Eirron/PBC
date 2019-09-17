# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr, nowdate
from workwise.payroll.payroll_utils import format_decimal_by_2, format_decimal_by_2_align_right
from frappe import _

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "pagibig_id",
			"label": _("Pag-IBIG ID"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "loan_type",
			"label": _("Loan Type"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "last_name",
			"label": _("Last Name"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "first_name",
			"label": _("First Name"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "name_extension",
			"label": _("Name Extension"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "middle_name",
			"label": _("Middle Name"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "percov",
			"label": _("PERCOV"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "amortization",
			"label": _("Amortization"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "remarks",
			"label": _("Remarks"),
			"fieldtype": "Data",
			"width": 200
		},		
	]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_loans(filters):
	loans = frappe.db.sql("""SELECT 
		PRE.`name`,
		PR.`employee`,
		TE.`hdmf_no` as pagibig_id,
		TE.`last_name`,
		TE.`first_name`,
		TE.`suffix` as name_extension,
		TE.`middle_name`,
		PRE.`amount`,
		LA.remarks,
		"PagIbig Loan" as loan_type,
		( SELECT payment_date FROM `tabLoan Application Payments` WHERE payment_status = 'PAID' AND `parent` = LA.`name` LIMIT 1 ) AS percov,
		( SELECT IFNULL(sum( payment_amount ), 0) FROM `tabLoan Application Payments` WHERE payment_status = 'PAID' AND `parent` = LA.`name` LIMIT 1 ) AS total_paid
		FROM `tabPayroll Register Entries` PRE
		INNER JOIN `tabPayroll Register` PR ON PRE.`parent` = PR.`name`
		INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		INNER JOIN `tabLoan Application` LA ON PRE.linked_document = LA.`name`
		WHERE PRE.pay_code = 'HDMFL'
		AND PR.company = %(company)s 
		AND PR.posting_date >= %(from_date)s 
		AND PR.posting_date <= %(to_date)s
		AND TE.is_active = 1
		{conditions}
		GROUP BY PRE.`name`
		ORDER BY PR.employee_name """.format(conditions=get_conditions(filters)),{ 
		"company": filters.company,
		"from_date": getdate(filters.from_date),
		"to_date": getdate(filters.to_date)
	}, as_dict=True)

	return loans

def get_conditions(filters):
	conditions = []
	if frappe.session.user != "Administrator":
		conditions.append(_("TE.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

	if filters.period_group:
		conditions.append(_("TE.`period_group` = '{0}'").format(filters.period_group))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

def get_data(filters):
	data = []
	data_entry = {}
	loans = get_loans(filters)

	if filters.include_header:
		hdmf_id = frappe.db.get_value("Company", filters.company, "hdmf_id")
		address = frappe.db.sql(""" SELECT DISTINCT(TA.`address_line1`) as address FROM `tabDynamic Link` DL JOIN `tabAddress` TA WHERE DL.`parenttype` = "Address" 
			AND DL.`link_doctype` = "Company" AND DL.`parent` = TA.`name` AND TA.`address_type` = "Registered" AND DL.`link_name` = %(company)s LIMIT 1 """, filters, as_dict=1)
		
		data += [
			{
				"hdmf_no": "Employer ID",
				"loan_type": hdmf_id,
				"last_name": "",
				"first_name": "",
				"name_extension": "",
				"middle_name": "",
				"percov": "",
				"amortization": "",
				"remarks": "",
			},
			{
				"hdmf_no": "Employer Name",
				"loan_type": filters.company,
				"last_name": "",
				"first_name": "",
				"name_extension": "",
				"middle_name": "",
				"percov": "",
				"amortization": "",
				"remarks": "",
			},
			{
				"hdmf_no": "Address",
				"loan_type": address[0] if address else "",
				"last_name": "",
				"first_name": "",
				"name_extension": "",
				"middle_name": "",
				"percov": "",
				"amortization": "",
				"remarks": "",
			},
		]

	for loan in loans:
		if loan['employee'] not in data_entry:
			percov = ""
			if loan['percov']:
				percov = datetime.datetime.strftime(loan['percov'],"%Y%m")

			data_entry[loan['employee']] = {
				"pagibig_id": loan["pagibig_id"],
				"loan_type": loan["loan_type"],
				"last_name": loan["last_name"],
				"first_name": loan["first_name"],
				"name_extension": loan["name_extension"],
				"middle_name": loan["middle_name"],
				"percov": percov,			
				"amortization": 0.00,
				"remarks": loan["remarks"]
			}
		data_entry[loan['employee']]['amortization'] += flt(loan['amount'], 8)

	for dat in data_entry:
		row = {
			"pagibig_id": data_entry[dat]["pagibig_id"],
			"loan_type": data_entry[dat]["loan_type"],
			"last_name": data_entry[dat]["last_name"],
			"first_name": data_entry[dat]["first_name"],
			"name_extension": data_entry[dat]["name_extension"],
			"middle_name": data_entry[dat]["middle_name"],
			"percov": data_entry[dat]["percov"],			
			"amortization": data_entry[dat]["amortization"],
			"remarks": data_entry[dat]["remarks"]
		}
		data.append(row)

	return data
 
def get_result_as_list(data, filters):
	result = []
	data = sorted(data, key = lambda k:k['last_name'])
	for d in data:
		row = {
			"pagibig_id": d.get("pagibig_id"),
			"loan_type": d.get("loan_type"),
			"last_name": d.get("last_name"),
			"first_name": d.get("first_name"),
			"name_extension": d.get("name_extension"),
			"middle_name": d.get("middle_name"),
			"percov": d.get("percov"),
			"amortization": format_decimal_by_2_align_right(d.get("amortization")) if d.get("amortization") else "",
			"remarks": d.get("remarks")
		}
		result.append(row)
		
	return result