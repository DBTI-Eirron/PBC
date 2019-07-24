# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class GovernmentCertificate(Document):
	def validate(self):
		self.validate_date()


	def validate_date(self):
		if self.from_date > self.to_date:
			frappe.throw(_("Invalidate from date and to date."))

	def get_employees(self):
		query = """SELECT EM.`name`, EM.`full_name`, PR.`name` as xname, PR.posting_date, """+self.add_amount()+""" FROM `tabEmployee` EM
		INNER JOIN `tabPayroll Register` PR ON EM.`name` = PR.employee
		WHERE EM.is_active = 1"""
		query += self.add_filter()
		employees = frappe.db.sql(query,as_dict=True)

		entries	= []
		for d in employees:
			total = d.employee + d.employer
			ec = 0
			if self.type == "SSS":
				total += d.ec
				ec += d.ec
			row = {
				"employee": d.name,
				"employee_name": d.full_name,
				"amount": total,
				"paid_date": d.posting_date,
				"er": d.employer,
				"ee": d.employee,
				"ec": ec

			}
			entries.append(row);

		for d in entries:
			row = self.append('employees', {})
			row.update(d)

	def add_filter(self):
		add_filter = " AND PR.posting_date >= '"+self.from_date+"' AND PR.posting_date <= '"+self.to_date+"'"
		if self.employee:
			add_filter += " AND EM.`name` = '"+self.employee+"'"
		if self.company:
			add_filter += " AND EM.company = '"+self.company+"'"
		if self.location:
			add_filter += " AND EM.location = '"+self.location+"'"
		if self.department:
			add_filter += " AND EM.department = '"+self.department+"'"

		if self.type =="SSS":
			add_filter += """ AND ((SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.parent = PR.name AND PRE.pay_code = 'SSS') +
			(SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.parent = PR.name AND PRE.pay_code = 'SSSE') +
			(SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.parent = PR.name AND PRE.pay_code = 'SSSC')) > 0"""
		elif self.type =="PHIC":
			add_filter += """ AND ((SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.parent = PR.name AND PRE.pay_code = "PHIC") +
			(SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.parent = PR.name AND PRE.pay_code = "PHICE")) > 0"""
		elif self.type =="HDMF":
			add_filter += """ AND ((SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.parent = PR.name AND PRE.pay_code = "HDMF") +
			(SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.parent = PR.name AND PRE.pay_code = "HDMFE")) > 0"""

		return add_filter

	def add_amount(self):
		if self.type =="SSS":
			add_amount = """(SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.pay_code = "SSS" AND PRE.parent = xname) as employee,
			(SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.pay_code = "SSSE" AND PRE.parent = xname) as employer,
			(SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.pay_code = "SSSC" AND PRE.parent = xname) as ec"""
		elif self.type =="PHIC":
			add_amount = """(SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.pay_code = "PHIC" AND PRE.parent = xname) as employee,
			(SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.pay_code = "PHICE" AND PRE.parent = xname) as employer"""
		elif self.type =="HDMF":
			add_amount = """(SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.pay_code = "HDMF" AND PRE.parent = xname) as employee,
			(SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.pay_code = "HDMFE" AND PRE.parent = xname) as employer"""
		return add_amount



