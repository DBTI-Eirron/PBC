# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe	import _

class PayrollRegister(Document):
	pass
@frappe.whitelist()
def get_period_status(period):
	freq = frappe.get_value("Payroll Period",period,"frequency")
	return freq