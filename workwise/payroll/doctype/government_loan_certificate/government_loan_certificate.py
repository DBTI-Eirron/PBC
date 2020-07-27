# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from workwise.time_keeping.application_utils import validate_inactive_employee

class GovernmentLoanCertificate(Document):
	def validate(self):
		validate_inactive_employee(self)
		self.validate_date()

	def validate_date(self):
		if self.from_date > self.to_date:
			frappe.throw(_("Invalidate from date and to date."))

	def get_employees(self):
		query = """SELECT EM.`name`, EM.`full_name`, PR.`name` as xname, PR.posting_date, EM.sensitivity, (SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.pay_code = '"""+self.type+"""' AND PRE.parent = xname) as amount 
		FROM  `tabPayroll Register` PR
		INNER JOIN `tabEmployee` EM ON PR.employee = EM.`name`
		WHERE EM.is_active = 1"""
		query += self.add_filter()
		employees = frappe.db.sql(query,as_dict=True)

		entries	= []
		if employees:
			for d in employees:
				row = {
					"employee": d.name,
					"employee_name": d.full_name,
					"amount": d.amount,
					"paid_date": d.posting_date,
					"sensitivity_level": d.sensitivity,
				}
				entries.append(row);
		else:
			frappe.throw(_("No Employee Found"))

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
		if self.sensitivity_level:
			add_filter += " AND EM.`sensitivity` = '"+self.sensitivity_level+"'"
		if frappe.session.user != "Administrator":
			add_filter += " AND EM.`sensitivity` IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE SU.allow_user = '"+frappe.session.user+"' )"
		if self.department:
			add_filter += " AND EM.department = '"+self.department+"'"
		add_filter += " AND (SELECT IFNULL(SUM(PRE.amount),0) FROM `tabPayroll Register Entries` PRE WHERE PRE.parent = PR.name AND PRE.pay_code = '"+self.type+"') > 0"
		return add_filter



