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
	if filters.type == "Detailed":
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
				"fieldname": "amortization",
				"label": _("Amortization"),
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
			{
				"fieldname": "loan_application",
				"label": _("Loan Application"),
				"fieldtype": "Data",
				"width": 140
			},	
		]
	else:
		columns = [
			{
				"fieldname": "loan_application",
				"label": _("Loan Application"),
				"fieldtype": "Link",
				"options": "Loan Application",
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
				"fieldname": "amortization",
				"label": _("Amortization"),
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
	data = []
	loan_list = []

	if filters.type == "Detailed":
		loans = frappe.db.sql("""SELECT 
			LA.`name`,
			LP.`payment_date` as posting_date, 
			LA.`loan_type`,
			LA.`loan_amount`,
			LA.`interest`,
			LA.`total_loan`,
			LP.`payment_amount` as amortization
			FROM `tabLoan Application Payments` LP 
			INNER JOIN `tabLoan Application` LA ON LP.`parent`=LA.`name` 
			INNER JOIN `tabEmployee` TE ON LA.`employee`=TE.`name`
			WHERE LP.`payment_status` = 'Paid' 
			AND TE.`user_id`=%(cur_user)s 
			AND LP.`payment_date` >= %(from_date)s AND LP.`payment_date` <= %(to_date)s
			GROUP BY LP.`name`
			ORDER BY LP.`payment_date` ASC """,{
			"cur_user": frappe.session.user,
			"from_date": getdate(filters.from_date),
			"to_date": getdate(filters.to_date),
		}, as_dict=True)

		loan_app = {}
		for l in loans:
			if l.name not in loan_app:
				loan_app.update({ l.name: 0.00 })
			loan_app[l.name] += flt(l.amortization, 8)

			loan = {
				"posting_date": l.posting_date,
				"loan_type": l.loan_type,
				"loan_amount": l.loan_amount,
				"interest": l.interest,
				"total_loan": l.total_loan,
				"amortization": l.amortization,
				"total_paid": loan_app[l.name],
				"total_unpaid": flt(l.total_loan, 8) - flt(loan_app[l.name], 8),
				"loan_application": l.name
			}
			data.append(loan)
	else:
		loans = frappe.db.sql("""SELECT 
			LA.`name`,
			LP.`payment_date` as posting_date, 
			LA.`loan_type`,
			LA.`loan_amount`,
			LA.`interest`,
			LA.`total_loan`,
			LP.`payment_amount`,
			LA.`unpaid_amount`,
			LA.`amortization`
			FROM `tabLoan Application Payments` LP 
			INNER JOIN `tabLoan Application` LA ON LP.`parent`=LA.`name` 
			INNER JOIN `tabEmployee` TE ON LA.`employee`=TE.`name`
			WHERE LP.`payment_status` = 'Paid' 
			AND TE.`user_id`=%(cur_user)s 
			AND LP.`payment_date` >= %(from_date)s AND LP.`payment_date` <= %(to_date)s
			GROUP BY LP.`name`
			ORDER BY LP.`payment_date` ASC """,{
			"cur_user": frappe.session.user,
			"from_date": getdate(filters.from_date),
			"to_date": getdate(filters.to_date),
		}, as_dict=True)

		loan_app = {}
		for l in loans:
			if l.name not in loan_app:
				loan_app.update({ l.name:{
						"loan_type": l.loan_type,
						"loan_amount": l.loan_amount,
						"interest": l.interest,
						"total_loan": l.total_loan,
						"amortization": l.amortization,
						"total_paid": 0.00,
						"total_unpaid": l.unpaid_amount,
					} 
				})
			loan_app[l.name]['total_paid'] += flt(l.payment_amount, 8)

		for dat in loan_app:
			row = {
				"loan_application": dat, 
				"loan_type": loan_app[dat]['loan_type'],
				"loan_amount": loan_app[dat]['loan_amount'],
				"interest": loan_app[dat]['interest'],
				"total_loan": loan_app[dat]['total_loan'],
				"amortization": loan_app[dat]['amortization'],
				"total_paid": loan_app[dat]['total_paid'],
				"total_unpaid": loan_app[dat]['total_unpaid'],
			}
			data.append(row)

	return data