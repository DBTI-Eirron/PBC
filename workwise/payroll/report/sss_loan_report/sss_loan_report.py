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
			"fieldname": "sss_id",
			"label": _("Employee SSS Number"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "last_name",
			"label": _("Employee Last Name"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "first_name",
			"label": _("Employee First Name"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "middle_initial",
			"label": _("Employee Middle Initial"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "loan_type",
			"label": _("Loan Type"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "loan_date",
			"label": _("Loan Date"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "loan_amount",
			"label": _("Loan Amount"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "penalty",
			"label": _("Penalty"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "amount_paid",
			"label": _("Amount Paid"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "ampsdg",
			"label": _("AMPSDG"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "remarks",
			"label": _("Remarks"),
			"fieldtype": "Data",
			"width": 120
		},
	]

	if filters.include_header:
		columns = [
			{
				"fieldname": "sss_id",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "last_name",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "first_name",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "middle_initial",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "loan_type",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "loan_date",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "loan_amount",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "penalty",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "amount_paid",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "ampsdg",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
			},
			{
				"fieldname": "remarks",
				"label": _(""),
				"fieldtype": "Data",
				"width": 120
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
			TE.sss_no as sss_id,
			TE.last_name as last_name,
			TE.first_name as first_name,
			UPPER( LEFT ( TE.middle_name, 1 ) ) as middle_initial,
			LA.loan_type as loan_type,
			LA.release_date as loan_date,
			LA.loan_amount as loan_amount,
			0.00 as penalty,
			PRE.amount as amount_paid,
			0.00 as ampsdg,
			LA.remarks as remarks
		FROM
			`tabPayroll Register` PR
			INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent`
			INNER JOIN `tabEmployee` TE ON PR.`employee` = TE.`name`
			INNER JOIN `tabLoan Application` LA ON PR.`employee` = LA.`employee` 
		WHERE
			PRE.pay_code = "SSSL"
			AND LA.loan_type = "SSSL"
			AND PR.`posting_date` BETWEEN %(from_date)s AND %(to_date)s
			AND PR.company = %(company)s
			AND LA.docstatus = 1
			AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(cur_user)s)
		ORDER BY
			PR.employee_name ASC """,{
				"company": filters.company,
				"cur_user": cur_user,
				"from_date": filters.from_date,
				"to_date": filters.to_date
			}, as_dict=True)
	else:
		loans = frappe.db.sql("""SELECT DISTINCT
			TE.sss_no as sss_id,
			TE.last_name as last_name,
			TE.first_name as first_name,
			UPPER( LEFT ( TE.middle_name, 1 ) ) as middle_initial,
			LA.loan_type as loan_type,
			LA.release_date as loan_date,
			LA.loan_amount as loan_amount,
			0.00 as penalty,
			PRE.amount as amount_paid,
			0.00 as ampsdg,
			LA.remarks as remarks
		FROM
			`tabPayroll Register` PR
			INNER JOIN `tabPayroll Register Entries` PRE ON PR.`name` = PRE.`parent`
			INNER JOIN `tabEmployee` TE ON PR.`employee` = TE.`name`
			INNER JOIN `tabLoan Application` LA ON PR.`employee` = LA.`employee` 
		WHERE
			PRE.pay_code = "SSSL"
			AND LA.loan_type = "SSSL"
			AND PR.`posting_date` BETWEEN %(from_date)s AND %(to_date)s
			AND PR.company = %(company)s
			AND LA.docstatus = 1
		ORDER BY
			PR.employee_name ASC """,{
				"company": filters.company,
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
	if filters.include_header:
		emp_count = 0
		total_amount_paid = 0
		for d in data:
			total_amount_paid += flt(d.total_paid, 8)
			emp_count += 1

		sss_id = frappe.db.get_value("Company", filters.company, "sss_id")
		address = frappe.db.sql_list("""SELECT DISTINCT(TA.`address_line1`) as address
			 FROM `tabDynamic Link` DL 
			 JOIN `tabAddress` TA WHERE DL.`parenttype` = "Address" 
			 AND DL.`link_doctype` = "Company" AND DL.`parent` = TA.`name` 
			 AND TA.`address_type` = "Registered" AND DL.`link_name` = %s LIMIT 1 """, filters.company)
		
		headers = [
			{
				"sss_id": "Employer ID Number",
				"last_name": sss_id,
				"first_name": "Employer Name",
				"middle_initial": filters.company,
				"loan_type": "Applicable Month",
				"loan_date": "",
				"loan_amount": "Branch Code",
				"penalty": "",
				"amount_paid": "",
				"ampsdg": "",
				"remarks": ""
			},
			{
				"sss_id": "Total Number of Employees",
				"last_name": emp_count,
				"first_name": "Total Penalty",
				"middle_initial": '{:,.2f}'.format(0),
				"loan_type": "Total Amount Paid",
				"loan_date": '{:,.2f}'.format(total_amount_paid),
				"loan_amount": "",
				"penalty": "",
				"amount_paid": "",
				"ampsdg": "",
				"remarks": ""
			},
			{
				"sss_id": "Employee SSS Number",
				"last_name": "Employee Last Name",
				"first_name": "Employee First Name",
				"middle_initial": "Employee Middle Initial",
				"loan_type": "Loan Type",
				"loan_date": "Loan Date",
				"loan_amount": "Loan Amount",
				"penalty": "Penalty",
				"amount_paid": "Amount Paid",
				"ampsdg": "AMPSDG",
				"remarks": "Remarks"
			},
		]

		for d in headers:
			result.append(d)

	for d in data:
		row = {
			"sss_id": d.get("sss_id"),
			"last_name": d.get("last_name"),
			"first_name": d.get("first_name"),
			"middle_initial": d.get("middle_initial"),
			"loan_type": d.get("loan_type"),
			"loan_date": datetime.datetime.strftime(getdate(d.get("loan_date")),"%y%m%d"),
			"loan_amount": '{:,.2f}'.format(d.get("loan_amount")),
			"penalty": '{:,.2f}'.format(d.get("penalty")),
			"amount_paid": '{:,.2f}'.format(d.get("amount_paid")),
			"ampsdg": '{:,.2f}'.format(d.get("ampsdg")),
			"remarks": d.get("remarks")
		}
		
		result.append(row)
		
	return result