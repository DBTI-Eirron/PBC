# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
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
				( SELECT payment_date FROM `tabLoan Application Payments` WHERE payment_status = 'PAID' AND `parent` = LA.`name` LIMIT 1 ) AS percov,
				( SELECT IFNULL(sum( payment_amount ), 0) FROM `tabLoan Application Payments` WHERE payment_status = 'PAID' AND `parent` = LA.`name` LIMIT 1 ) AS total_paid 
			FROM
				`tabLoan Application` AS LA
				INNER JOIN `tabEmployee` AS TE ON TE.`name` = LA.employee 
			WHERE
				LA.loan_type = "HDMFL"
				AND LA.`posting_date` BETWEEN %(from_date)s AND %(to_date)s
				AND LA.company = %(company)s 
				AND LA.docstatus = 1 
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
						INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
			ORDER BY
				LA.employee_name ASC """,{
						"company": filters.company,
						"cur_user": frappe.session.user,
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
				( SELECT payment_date FROM `tabLoan Application Payments` WHERE payment_status = 'PAID' AND `parent` = LA.`name` LIMIT 1 ) AS percov,
				( SELECT IFNULL(sum( payment_amount ), 0) FROM `tabLoan Application Payments` WHERE payment_status = 'PAID' AND `parent` = LA.`name` LIMIT 1 ) AS total_paid 
			FROM
				`tabLoan Application` AS LA
				INNER JOIN `tabEmployee` AS TE ON TE.`name` = LA.employee 
			WHERE
				LA.loan_type = "HDMFL"
				AND LA.`posting_date` BETWEEN %(from_date)s AND %(to_date)s
				AND LA.company = %(company)s 
				AND LA.docstatus = 1 
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
						INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
			ORDER BY
				LA.employee_name ASC """,{
						"company": filters.company,
						"cur_user": frappe.session.user,
						"from_date": filters.from_date,
						"to_date": filters.to_date
			}, as_dict=True)

	return loans

def get_data(filters):
	data = []
	loans = get_loans(filters)

	for loan in loans: 
		data.append(loan)

	return data
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		percov = ""
		percov = d.get("percov")
		percov = datetime.datetime.strftime(percov,"%Y%m")
		row = {
			"pagibig_id": d.get("hdmf_no"),
			"loan_type": "PagIbig Loan",
			"last_name": d.get("last_name"),
			"first_name": d.get("first_name"),
			"name_extension": d.get("suffix"),
			"middle_name": d.get("middle_name"),
			"percov": percov,			
			"amortization": d.get("amortization"),
			"remarks": d.get("remarks")
		}
		
		result.append(row)
		
	return result