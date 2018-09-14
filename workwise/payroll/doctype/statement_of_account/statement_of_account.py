# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class StatementofAccount(Document):
	def validate(self):
		self.get_netpayroll()
		#self.get_prepared_by()

	def get_netpayroll(self):
		from frappe.utils import money_in_words

		net_payroll = 0.0
		register = frappe.db.sql(""" SELECT PR.employee, PR.employee_name, PR.net_payroll, E.cost_center
			FROM `tabPayroll Register` PR 
			INNER JOIN tabEmployee E ON E.`name` = PR.employee WHERE E.cost_center = %s AND PR.period = %s """, (self.cost_center, self.period), as_dict=1)

		for d in register:
			net_payroll += d.net_payroll

		self.total_payroll = net_payroll
		self.in_words = money_in_words(net_payroll, 'PHP')
		
