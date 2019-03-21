# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr, nowdate
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
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		loans = frappe.db.sql("""SELECT DISTINCT
				LA.`name`,
				LA.employee,
				LA.employee_name,
				LA.posting_date,
				LA.interest,
				LA.loan_type,
				LA.loan_amount,
				LA.total_loan,
				LA.amortization,
				LA.remarks,
				TE.last_name,
				TE.first_name,
				TE.middle_name,
				TE.suffix,
				TE.hdmf_no,
				"PagIbig Loan" as loan_type,
				( SELECT payment_date FROM `tabLoan Application Payments` WHERE payment_status = 'PAID' AND `parent` = LA.`name` LIMIT 1 ) AS percov,
				( SELECT IFNULL(sum( payment_amount ), 0) FROM `tabLoan Application Payments` WHERE payment_status = 'PAID' AND `parent` = LA.`name` LIMIT 1 ) AS total_paid 
			FROM
				`tabLoan Application` AS LA
				INNER JOIN `tabEmployee` AS TE ON LA.employee = TE.`name` INNER JOIN `tabPayroll Register` PR ON LA.employee = PR.employee
			WHERE
				LA.loan_type = "HDMFL"
				AND LA.`posting_date` BETWEEN %(from_date)s AND %(to_date)s
				AND PR.company = %(company)s 
				AND LA.docstatus = 1 
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(cur_user)s)
			ORDER BY
				LA.employee_name ASC """,{
						"company": filters.company,
						"cur_user": cur_user,
						"from_date": filters.from_date,
						"to_date": filters.to_date
			}, as_dict=True)
	else:
		loans = frappe.db.sql("""SELECT DISTINCT
				LA.`name`,
				LA.employee,
				LA.employee_name,
				LA.posting_date,
				LA.interest,
				LA.loan_type,
				LA.loan_amount,
				LA.total_loan,
				LA.amortization,
				LA.remarks,
				TE.last_name,
				TE.first_name,
				TE.middle_name,
				TE.suffix,
				TE.hdmf_no,
				"PagIbig Loan" as loan_type,
				( SELECT payment_date FROM `tabLoan Application Payments` WHERE payment_status = 'PAID' AND `parent` = LA.`name` LIMIT 1 ) AS percov,
				( SELECT IFNULL(sum( payment_amount ), 0) FROM `tabLoan Application Payments` WHERE payment_status = 'PAID' AND `parent` = LA.`name` LIMIT 1 ) AS total_paid 
			FROM
				`tabLoan Application` AS LA
				INNER JOIN `tabEmployee` AS TE ON LA.employee = TE.`name` INNER JOIN `tabPayroll Register` PR ON LA.employee = PR.employee
			WHERE
				LA.loan_type = "HDMFL"
				AND LA.`posting_date` BETWEEN %(from_date)s AND %(to_date)s
				AND PR.company = %(company)s 
				AND LA.docstatus = 1
			ORDER BY
				LA.employee_name ASC """,{
						"company": filters.company,
						"from_date": filters.from_date,
						"to_date": filters.to_date
			}, as_dict=True)

	return loans

def get_data(filters):
	data = []
	loans = get_loans(filters)

	if filters.include_header:
		hdmf_id = frappe.db.get_value("Company", filters.company, "hdmf_id")
		address = frappe.db.sql_list("""SELECT DISTINCT(TA.`address_line1`) as address
			 FROM `tabDynamic Link` DL 
			 JOIN `tabAddress` TA WHERE DL.`parenttype` = "Address" 
			 AND DL.`link_doctype` = "Company" AND DL.`parent` = TA.`name` 
			 AND TA.`address_type` = "Registered" AND DL.`link_name` = %s LIMIT 1 """, filters.company)
		
		headers = [
			{
				"hdmf_no": "Employer ID",
				"loan_type": hdmf_id 
			},
			{
				"hdmf_no": "Employer Name",
				"loan_type": filters.company
			},
			{
				"hdmf_no": "Address",
				"loan_type": address[0] if address else ""
			},
		]

		for d in headers:
			data.append(d)

	for loan in loans: 
		data.append(loan)



	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		percov = ""
		if d.get("percov"):
			percov = datetime.datetime.strftime(d.get("percov"),"%Y%m")

		row = {
			"pagibig_id": d.get("hdmf_no"),
			"loan_type": d.get("loan_type"),
			"last_name": d.get("last_name"),
			"first_name": d.get("first_name"),
			"name_extension": d.get("suffix"),
			"middle_name": d.get("middle_name"),
			"percov": percov,			
			"amortization": '{:20,.2f}'.format(flt(d.get("amortization"))),
			"remarks": d.get("remarks")
		}
		
		result.append(row)
		
	return result