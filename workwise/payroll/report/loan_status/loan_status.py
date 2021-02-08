# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from workwise.payroll.payroll_utils import format_precision, format_align_right
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
			"fieldtype": "Data",
			"width": 140
		},		
		{
			"fieldname": "interest",
			"label": _("Interest"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "total_loan",
			"label": _("Total Loan"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "total_paid",
			"label": _("Total Paid Amount"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "total_unpaid",
			"label": _("Total Unpaid Amount"),
			"fieldtype": "Data",
			"width": 140
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
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
		loans = frappe.db.sql("""SELECT DISTINCT
				LA.`name`,
				LA.employee,
				LA.employee_name,
				LA.posting_date,
				LA.interest,
				LA.loan_type,
				LA.loan_amount,
				LA.total_loan,
				LA.paid_amount,
				LA.unpaid_amount,
				LA.on_hold

			FROM `tabPayroll Register Entries` PE
				INNER JOIN `tabLoan Application` LA ON PE.`linked_document`=LA.`name`
				INNER JOIN `tabPayroll Register` PR ON PE.`parent`=PR.`name`

			WHERE
				LA.company = %(company)s 
				AND LA.docstatus = 1 
				AND (PR.`posting_date` BETWEEN %(from_date)s AND %(to_date)s)
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
		loans = frappe.db.sql("""SELECT DISTINCT
				LA.`name`,
				LA.employee,
				LA.employee_name,
				LA.posting_date,
				LA.interest,
				LA.loan_type,
				LA.loan_amount,
				LA.total_loan,
				LA.paid_amount,
				LA.unpaid_amount,
				LA.on_hold
				
			FROM `tabPayroll Register Entries` PE
				INNER JOIN `tabLoan Application` LA ON PE.`linked_document`=LA.`name`
				INNER JOIN `tabPayroll Register` PR ON PE.`parent`=PR.`name`
				INNER JOIN `tabEmployee` TE ON PR.`employee`=TE.`name`

			WHERE
				LA.company = %(company)s 
				AND LA.docstatus = 1 
				AND (PR.`posting_date` BETWEEN %(from_date)s AND %(to_date)s)
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

	for l in loans:
		total_loans = get_loan_amount(filters, l)
		l['total_paid'] = flt(total_loans)

	for loan in loans: 
		data.append(loan)

	return data

def get_loan_amount(filters, loan):
	loan_amount = frappe.db.sql(""" SELECT 
		SUM(PE.`amount`) as `amount`
		FROM `tabPayroll Register Entries` PE
		INNER JOIN `tabPayroll Register` PR ON PE.`parent`=PR.`name`
		WHERE PE.`linked_doctype`='Loan Application'
		AND PE.`linked_document`= %(application)s
		AND PR.company = %(company)s
		AND (PR.`posting_date` BETWEEN %(from_date)s AND %(to_date)s)
		GROUP BY PE.`linked_document` """,{
		"application": loan.name,
		"company": filters.company,
		"from_date": filters.from_date,
		"to_date": filters.to_date
	}, as_dict=True)

	if loan_amount:
		loan_amount = loan_amount[0].amount
	else:
		loan_amount = 0.00

	return loan_amount
 
def get_result_as_list(data, filters):
	result = []
	for d in data:
		if d.on_hold == 1:
			status = "On Hold"
		if d.paid_amount < 1 and d.on_hold != 1:
			status = "Entered"
		if d.paid_amount > 0 and d.on_hold != 1:
			status = "Active"
		if d.paid_amount == d.loan_amount and d.on_hold != 1:
			status = "Fully Paid"

		row = {
			"employee": d.get("employee"),
			"employee_name": d.get("employee_name"),
			"posting_date": d.get("posting_date"),
			"loan_type": d.get("loan_type"),
			"loan_amount": format_precision(d.get("loan_amount"), filters.value_precision),
			"interest": format_precision(d.get("interest"), filters.value_precision),
			"total_loan": format_precision(d.get("total_loan"), filters.value_precision),			
			"total_paid": format_precision(d.get("total_paid"), filters.value_precision),
			"total_unpaid": format_precision(d.get("total_loan") - d.get("total_paid"), filters.value_precision),
			"status": status
		}
		
		result.append(row)
		
	return result