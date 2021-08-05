from __future__ import unicode_literals
import frappe, datetime
from datetime import time, datetime
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _

def get_loans_map(employees, payroll_date, period_from, period_to):
	#Create Loans Map
	loans_map = frappe._dict()
	for emp in employees:
		reload_loans(emp.name, payroll_date)
		loans_map.setdefault(emp.name, frappe._dict({
				"automatic_loans": [],
				"dated_loans": [],
			})
		)

	#Get Automatic Loans
	automatic_loans = frappe.db.sql(""" SELECT LA.`name`, LA.employee, LA.loan_type, LA.loan_amount, LA.payment_frequency, MAX(LAP.payment_amount) as payment_amount, 
		MIN(LAP.idx) as idx
		FROM `tabLoan Application` LA 
		INNER JOIN `tabLoan Application Payments` LAP ON LA.`name` = LAP.parent
		INNER JOIN `tabTransaction Type` TT ON LA.loan_type = TT.`name`
		WHERE LA.payment_start <= %s AND LA.freq_method = 'Automatic' AND LAP.payment_status = 'Unpaid' AND LA.docstatus = 1 AND on_hold != 1 AND TT.is_active = 1
		GROUP BY LA.`name` ORDER BY LAP.idx """, ( getdate(payroll_date) ), as_dict=True)

	for d in automatic_loans:
		if d.employee in loans_map:
			loans_map[d.employee].automatic_loans.append(d)

	#Get Dated Loans
	dated_loans = frappe.db.sql(""" SELECT LA.`name`, LA.employee, LAP.due_date, LA.loan_type, LAP.payment_amount, LAP.idx
		FROM `tabLoan Application` LA
		INNER JOIN `tabLoan Application Payments` LAP ON LA.`name` = LAP.parent
		INNER JOIN `tabTransaction Type` TT ON LA.loan_type = TT.`name`
		WHERE LAP.due_date >= %s AND LAP.due_date <= %s AND LA.freq_method != 'Automatic' AND LAP.payment_status = 'Unpaid' AND LA.docstatus = 1 AND TT.is_active = 1
		AND on_hold != 1
		ORDER BY LAP.idx """, ( getdate(period_from), getdate(period_to) ), as_dict=True)

	for d in dated_loans:
		if d.employee in loans_map:
			loans_map[d.employee].dated_loans.append(d)

	return loans_map

def get_employee_loan(emp, header, register, loans_map, frequency):
	loans_register = []

	def append_al(al, loans_register):
		loans_register.append({
				"linked_document": al.name,
				"linked_doctype": "Loan Application",
				"loan_idx": al.idx,
				"pay_code": al.loan_type,
				"amount": flt(al.payment_amount, 8),
			})		

	if emp.get('name') in loans_map:
		#automatic loans
		for al in loans_map[emp.get('name')].automatic_loans:
			if emp.get('payroll_schedule') == "Weekly":
				if al.payment_frequency == 'Both':
					if cint(header.get("no_weeks")) == cint(5):
						if frequency in ["2nd", "5th"]:
							append_al(al, loans_register)
					elif cint(header.get("no_weeks")) == cint(4):
						if frequency in ["2nd", "4th"]:
							append_al(al, loans_register)
				
				if al.payment_frequency == '1st' and frequency == '2nd':
					append_al(al, loans_register)
				
				if al.payment_frequency == '2nd':
					if cint(header.get("no_weeks")) == cint(5) and frequency == "5th":
						append_al(al, loans_register)

					elif cint(header.get("no_weeks")) == cint(4) and frequency == "4th":
						append_al(al, loans_register)
			else:
				if str(al.payment_frequency).strip() == str(frequency).strip() or str(al.payment_frequency).strip() == 'Both':
					append_al(al, loans_register)
		#dated loans
		for dl in loans_map[emp.get('name')].dated_loans:
			loans_register.append({
					"linked_document": dl.name,
					"linked_doctype": "Loan Application",
					"loan_idx": dl.idx,
					"pay_code": dl.loan_type,	
					"amount": flt( dl.payment_amount, 8),
				})

	for lr in loans_register:
		register.append(lr)

def reload_loans(employee_name, payroll_date):
	frappe.db.sql("""UPDATE `tabLoan Application Payments` LAP INNER JOIN `tabLoan Application` LA ON LAP.parent = LA.name SET LAP.payment_status = 'Unpaid', 
		LAP.payment_date = NULL WHERE LA.employee = %s AND LAP.payment_date = %s AND LAP.payment_status = 'Paid' """,( employee_name, payroll_date), as_dict=True )

def update_loans(payroll_date, loan_doc, loan_idx, period):
	if loan_doc and frappe.get_all("Loan Application", filters={"name": loan_doc}):
		total_paid, total_unpaid = 0, 0
		frappe.db.sql("""UPDATE `tabLoan Application Payments` SET payment_status = 'Paid', payment_date = %s, payroll_period = %s
			WHERE parent = %s AND idx = %s AND payment_status = 'Unpaid'   """,(payroll_date, period, loan_doc, loan_idx), as_dict=True )

		payments = frappe.db.sql("""SELECT payment_status, payment_amount FROM `tabLoan Application Payments` 
			WHERE parent = %s""",(loan_doc), as_dict=True )
		
		for p in payments:
			if p.payment_status == 'Paid':
				total_paid += p.payment_amount
			else:
				total_unpaid += p.payment_amount

		frappe.db.sql("""UPDATE `tabLoan Application` SET unpaid_amount = %s, paid_amount = %s
			WHERE name = %s LIMIT 1 """,(total_unpaid, total_paid, loan_doc), as_dict=True )

		doc = frappe.get_doc("Loan Application", loan_doc)
		doc.run_method("update_loan_status")