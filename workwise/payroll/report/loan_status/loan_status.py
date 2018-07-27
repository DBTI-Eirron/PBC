# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

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
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 130
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "posting_date",
			"label": _("Posting Date"),
			"fieldtype": "Date",
			"width": 140
		},
		{
			"fieldname": "loan_type",
			"label": _("Loan Type"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "loan_amount",
			"label": _("Loan Amount"),
			"fieldtype": "Float",
			"width": 140
		},		
		{
			"fieldname": "interest",
			"label": _("Interest"),
			"fieldtype": "Float",
			"width": 140
		},
		{
			"fieldname": "total_loan",
			"label": _("Total Loan"),
			"fieldtype": "Float",
			"width": 140
		},
		{
			"fieldname": "total_paid",
			"label": _("Total Paid Amount"),
			"fieldtype": "Float",
			"width": 140
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
		loans = frappe.db.sql("""SELECT
				LA.`name`,
				LA.employee,
				LA.employee_name,
				LA.posting_date,
				LA.interest,
				LA.loan_type,
				LA.loan_amount,
				LA.total_loan,
				( SELECT IFNULL(sum( payment_amount ), 0) FROM `tabLoan Application Payments` WHERE payment_status = 'PAID' AND `parent` = LA.`name` ) AS total_paid 
			FROM
				`tabLoan Application` AS LA
				INNER JOIN `tabEmployee` AS TE ON TE.`name` = LA.employee 
			WHERE
				LA.company = %(company)s 
				AND LA.docstatus = 1 
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
						INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`
						WHERE SU.allow_user = %(cur_user)s)
			ORDER BY
				LA.employee_name ASC """,{
						"company": filters.company,
						"cur_user": frappe.session.user,
						"from_date": filters.from_date,
						"to_date": filters.to_date,
			}, as_dict=True)
	else:
		loans = frappe.db.sql("""SELECT
				LA.`name`,
				LA.employee,
				LA.employee_name,
				LA.posting_date,
				LA.interest,
				LA.loan_type,
				LA.loan_amount,
				LA.total_loan,
				( SELECT IFNULL(sum( payment_amount ), 0) FROM `tabLoan Application Payments` WHERE payment_status = 'PAID' AND `parent` = LA.`name` ) AS total_paid 
			FROM
				`tabLoan Application` AS LA
				INNER JOIN `tabEmployee` AS TE ON TE.`name` = LA.employee 
			WHERE
				LA.company = %(company)s 
				AND LA.docstatus = 1 
				AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL 
						INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name`)
			ORDER BY
				LA.employee_name ASC """,{
						"company": filters.company,
						"cur_user": frappe.session.user,
						"from_date": filters.from_date,
						"to_date": filters.to_date,
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
		row = {
			"employee": d.get("employee"),
			"employee_name": d.get("employee_name"),
			"posting_date": d.get("posting_date"),
			"loan_type": d.get("loan_type"),
			"loan_amount": d.get("loan_amount"),
			"interest": d.get("interest"),
			"total_loan": d.get("total_loan"),			
			"total_paid": d.get("total_paid")
		}
		
		result.append(row)
		
	return result