# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr, nowdate
from workwise.payroll.payroll_utils import format_precision, format_align_right
from frappe import _

def execute(filters=None):
	
	if not filters: filters = frappe._dict({})
	validate_filters(filters)

	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	data = []
	data_entry = {}
	employees = get_employees(filters)
	emp_count = 0
	if filters.include_header:
		total_amount_paid = 0
		for e in employees:
			total_amount_paid += e.amount_paid

		company = frappe.db.sql("""SELECT TC.sss_id,TC.phone, TA.address_title, TA.city, TA.pincode FROM `tabCompany` TC LEFT JOIN `tabDynamic Link` DL 
			ON TC.`name` = DL.link_name LEFT JOIN `tabAddress` TA ON DL.parent = TA.`name` LIMIT 1 """, as_dict=True)
		if company:
			address = str(company[0]['address_title'])+", "+str(company[0]['city'])
			zipcode = str(company[0]['pincode'])
			contact = str(company[0]['phone'])
			com_id = str(company[0]['sss_id'])
		else:
			address = ""
			zip_code = ""
			contact = ""
			com_id = ""
	
		data += [
			{
				"sss_id": "Employer ID Number",
				"last_name": com_id,
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

	included_loan = []
	total_loan_amount = 0.00
	total_paid_amount = 0.00
	row = []
	for emp in employees: 
		if emp['employee'] not in data_entry:
			emp_count += 1
			data_entry[emp['employee']] = {
				"sss_id": emp['sss_id'],
				"last_name": emp['last_name'],
				"first_name": emp['first_name'],
				"middle_initial": emp['middle_initial'],
				"loan_type": emp['loan_type'],
				"loan_date": emp['loan_date'],
				"loan_amount": flt(emp['loan_amount'], 8),
				"penalty": 0.00,
				"amount_paid": 0.00,
				"ampsdg": 0.00,
				"remarks": emp['remarks'],
			}
		data_entry[emp['employee']]['penalty'] += flt(emp['penalty'], 8)
		data_entry[emp['employee']]['amount_paid'] +=  flt(emp['amount_paid'], 8)
		data_entry[emp['employee']]['ampsdg'] += flt(emp['ampsdg'], 8)
		if emp.linked_document not in included_loan:
			total_loan_amount += flt(emp['loan_amount'], 6)
			included_loan.append(emp.linked_document)

	for dat in data_entry:
		total_paid_amount += data_entry[dat]['amount_paid']
		row.append({
			"sss_id": data_entry[dat]['sss_id'],
			"last_name": data_entry[dat]['last_name'],
			"first_name": data_entry[dat]['first_name'],
			"middle_initial": data_entry[dat]['middle_initial'],
			"loan_type": data_entry[dat]['loan_type'],
			"loan_date": data_entry[dat]['loan_date'],
			"loan_amount": format_align_right(format_precision(data_entry[dat]['loan_amount'], filters.value_precision)),
			"penalty": format_align_right(format_precision(data_entry[dat]['penalty'], filters.value_precision)),
			"amount_paid": format_align_right(format_precision(data_entry[dat]['amount_paid'], filters.value_precision)),
			"ampsdg": format_align_right(format_precision(data_entry[dat]['ampsdg'], filters.value_precision)),
			"remarks": data_entry[dat]['remarks'],
		})
	row = sorted(row, key = lambda k:k['last_name'])
	for r in row:
		data.append(r)
	if filters.include_header:
		data.append({
			"sss_id": "Total Number of Employees",
			"last_name": emp_count,
			"first_name": "Total Penalty",
			"middle_initial": format_precision(0, filters.value_precision),
			"loan_type": "Total Amount Paid",
			"loan_date": format_precision(total_amount_paid, filters.value_precision),
			"loan_amount": "",
			"penalty": "",
			"amount_paid": "",
			"ampsdg": "",
			"remarks": ""
		})
	data.append({
				"sss_id": "Total", 
				"loan_amount": format_align_right(format_precision(total_loan_amount, filters.value_precision)), 
				"amount_paid": format_align_right(format_precision(total_paid_amount, filters.value_precision)) if not filters.include_header else ""
				})

	return data

def get_employees(filters):
	employees = frappe.db.sql("""SELECT 
		PRE.`name`,
		PR.`employee`,
		TE.sss_no as sss_id,
		TE.last_name,
		TE.first_name,
		LEFT(TE.middle_name, 1) as middle_initial,
		LA.loan_type,
		LA.release_date as loan_date,
		LA.loan_amount,
		0.00 as penalty,
		PRE.amount as amount_paid,
		0.00 as ampsdg,
		LA.remarks,
		PRE.linked_document
		FROM `tabPayroll Register Entries` PRE
		INNER JOIN `tabPayroll Register` PR ON PRE.`parent` = PR.`name`
		INNER JOIN `tabEmployee` TE ON PR.employee = TE.`name`
		INNER JOIN `tabLoan Application` LA ON PRE.linked_document = LA.`name`
		WHERE PRE.pay_code = 'SSSCL'
		AND PR.company = %(company)s 
		AND PR.posting_date >= %(from_date)s 
		AND PR.posting_date <= %(to_date)s
		{conditions}
		GROUP BY PRE.`name`
		ORDER BY PR.employee_name""".format(conditions=get_conditions(filters)),{ 
		"company": filters.company,
		"from_date": getdate(filters.from_date),
		"to_date": getdate(filters.to_date)
	}, as_dict=True)

	if not employees:
		frappe.throw(_("No Records Found"))

	return employees

def get_conditions(filters):
	conditions = []
	if frappe.session.user != "Administrator":
		conditions.append(_("TE.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

	if filters.period_group:
		conditions.append(_("TE.`period_group` = '{0}'").format(filters.period_group))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

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
