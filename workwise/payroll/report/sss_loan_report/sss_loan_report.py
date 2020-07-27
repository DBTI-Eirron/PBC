# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr, nowdate
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_data(filters)

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

def get_employees(filters):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		employees = frappe.db.sql(""" SELECT 
			LA.`name`,
			TE.`name` as employee,
			TE.sss_no as sss_id,
			TE.last_name as last_name,
			TE.first_name as first_name,
			UPPER( LEFT ( TE.middle_name, 1 ) ) as middle_initial,
			LA.loan_type as loan_type,
			LA.release_date as loan_date,
			LA.loan_amount as loan_amount,
			LA.remarks as remarks
			FROM `tabPayroll Register Entries` PE
			INNER JOIN `tabLoan Application` LA ON PE.`linked_document`=LA.`name`
			INNER JOIN `tabPayroll Register` PR ON PE.`parent`=PR.`name`
			INNER JOIN `tabEmployee` TE ON PR.`employee`=TE.`name`
			WHERE LA.`loan_type`='SSSL'
			AND TE.company = %(company)s
			AND (PR.`posting_date` BETWEEN %(from_date)s AND %(to_date)s)
			AND TE.sensitivity IN (SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = %(cur_user)s)
			GROUP BY LA.`name`
			ORDER BY LA.`employee_name` ASC """,{
			"company": filters.company,
			"cur_user": cur_user,
			"from_date": filters.from_date,
			"to_date": filters.to_date
		}, as_dict=True)
	else:
		employees = frappe.db.sql(""" SELECT 
			LA.`name`,
			TE.`name` as employee,
			TE.sss_no as sss_id,
			TE.last_name as last_name,
			TE.first_name as first_name,
			UPPER( LEFT ( TE.middle_name, 1 ) ) as middle_initial,
			LA.loan_type as loan_type,
			LA.release_date as loan_date,
			LA.loan_amount as loan_amount,
			LA.remarks as remarks
			FROM `tabPayroll Register Entries` PE
			INNER JOIN `tabLoan Application` LA ON PE.`linked_document`=LA.`name`
			INNER JOIN `tabPayroll Register` PR ON PE.`parent`=PR.`name`
			INNER JOIN `tabEmployee` TE ON PR.`employee`=TE.`name`
			WHERE LA.`loan_type`='SSSL'
			AND TE.company = %(company)s
			AND (PR.`posting_date` BETWEEN %(from_date)s AND %(to_date)s)
			GROUP BY LA.`name`
			ORDER BY LA.`employee_name` ASC """,{
			"company": filters.company,
			"from_date": filters.from_date,
			"to_date": filters.to_date
		}, as_dict=True)

	return employees

def get_loan_amount(filters, emp):
	loan_amount = frappe.db.sql(""" SELECT 
		SUM(PE.`amount`) as `amount`
		FROM `tabPayroll Register Entries` PE
		INNER JOIN `tabPayroll Register` PR ON PE.`parent`=PR.`name`
		WHERE PE.`pay_code`='SSSL'
		AND PE.`linked_doctype`='Loan Application'
		AND PE.`linked_document`= %(application)s
		AND PR.company = %(company)s
		AND (PR.`posting_date` BETWEEN %(from_date)s AND %(to_date)s)
		GROUP BY PE.`linked_document` """,{
		"application": emp.name,
		"company": filters.company,
		"from_date": filters.from_date,
		"to_date": filters.to_date
	}, as_dict=True)

	if loan_amount:
		loan_amount = loan_amount[0].amount
	else:
		loan_amount = 0.00

	return loan_amount

def get_data(filters):
	data = []
	employees = get_employees(filters)

	if filters.include_header:
		emp_count = 0
		total_amount_paid = 0
		for d in employees:
			loans = get_loan_amount(filters, d)
			total_amount_paid += flt(loans)
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
				"middle_initial": 0,
				"loan_type": "Total Amount Paid",
				"loan_date": format_precision(total_amount_paid, filters.value_precision),
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
			data.append(d)

	for emp in employees: 
		loans = get_loan_amount(filters, emp)
		date = None
		if filters.date_format == "1":
			date = datetime.datetime.strftime(getdate(emp.loan_date),"%y%m%d") 
		if filters.date_format == "2":
			date = datetime.datetime.strftime(getdate(emp.loan_date),"%m%d%y")
		if filters.date_format == "3":
			date = datetime.datetime.strftime(getdate(emp.loan_date),"%m-%d-%y") 
		row = {
			"sss_id": emp.sss_id,
			"last_name": emp.last_name,
			"first_name": emp.first_name,
			"middle_initial": emp.middle_initial,
			"loan_type": emp.loan_type,
			"loan_date": date,
			"loan_amount": format_precision(emp.loan_amount, filters.value_precision),
			"penalty": 0,
			"amount_paid": format_precision(loans, filters.value_precision),
			"ampsdg": 0,
			"remarks": emp.remarks,
		}
		data.append(row)

	return data