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
		{
			"fieldname": "total_unpaid",
			"label": _("Total Unpaid Amount"),
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
			TE.user_id = %(cur_user)s 
			AND LA.docstatus = 1 
		ORDER BY
			LA.employee_name ASC """,{
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
			"posting_date": d.get("posting_date"),
			"loan_type": d.get("loan_type"),
			"loan_amount": d.get("loan_amount"),
			"interest": d.get("interest"),
			"total_loan": d.get("total_loan"),			
			"total_paid": d.get("total_paid"),
			"total_unpaid": flt(d.get("total_loan"), 2) - flt(d.get("total_paid"), 2)
		}
		
		result.append(row)
		
	return result