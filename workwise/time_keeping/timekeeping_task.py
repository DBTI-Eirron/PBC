# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe.utils import datediff, nowdate, format_date, add_days

def auto_timecard(self):
	pr = frappe.new_doc("Payroll Register")
	pr.update({
		"date": "2018-02-15",
		"time": "08:00:00",
		"biometrics_id": 7777,
		"card_type": 7,
	})
	pr.insert()