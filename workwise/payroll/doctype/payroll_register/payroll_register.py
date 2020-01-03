# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from frappe	import _

class PayrollRegister(Document):
	def on_trash(self):
		for d in self.payroll_register_entries:
			if d.entry_type == 'Loan' and d.linked_doctype == 'Loan Application' and d.linked_document: 
				is_deleted = frappe.db.sql("""UPDATE `tabLoan Application Payments` LP INNER JOIN `tabLoan Application` LA ON LP.`parent`=LA.`name` 
					SET LP.`payment_status`='Unpaid', LP.`payment_date` = NULL, LA.`unpaid_amount` = LA.`unpaid_amount`+LP.`payment_amount`, LA.`paid_amount` = LA.`paid_amount`-LP.`payment_amount`
					WHERE LP.`parent` = %s AND LA.`employee` = %s AND LP.`payment_date` = %s """,(d.linked_document, self.employee, getdate(self.posting_date) ))

@frappe.whitelist()
def get_period_status(period):
	freq = frappe.get_value("Payroll Period",period,"frequency")
	return freq