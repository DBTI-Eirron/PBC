# -*- coding: utf-8 -*-
# Copyright (c) 2020, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from workwise.time_keeping.timekeeping_task import automated_leave_balance

class TimekeepingTools(Document):
	def force_lb_scheduler(self):
		if automated_leave_balance(1):
		 	frappe.msgprint('LB Entries created')
		else:
			frappe.throw('No LB Entry created')