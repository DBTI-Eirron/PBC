# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, nowdate
from frappe.model.document import Document

class BatchApproval(Document):
	def validate(self):
		pass

	def on_submit(self):
		self.approve_applications()

	def map_applications_on_table(self):
		self.set('batch_table', [])
		table = "`tab"+self.application_type+"`"
		table = str(table)
		if self.employee:
			record = frappe.db.sql("""SELECT AP.`name`, AP.`posting_date`, AP.`employee`, TE.`full_name` FROM """+table+""" AP JOIN `tabEmployee` TE WHERE AP.`employee` = TE.`name` AND AP.`docstatus` = 0 AND (AP.`posting_date` BETWEEN %s AND %s) AND AP.`employee` = %s """, (getdate(self.from_date), getdate(self.to_date), self.employee), as_dict=True)
		else:
			cur_user = frappe.session.user
			if not "Administrator" in frappe.get_roles(cur_user):
				record = frappe.db.sql(""" SELECT DISTINCT AP.`name`, AP.`posting_date`, AP.`employee`, TE.`full_name` FROM """+table+""" AP JOIN `tabEmployee` TE ON AP.`employee` = TE.`name` WHERE AP.`docstatus` = 0 AND (AP.`posting_date` BETWEEN %s AND %s) AND TE.`name` IN (SELECT `for_value` FROM `tabUser Permission` WHERE `allow` = "Employee" AND `user` = %s) """, (getdate(self.from_date), getdate(self.to_date), cur_user), as_dict=True)
			else:
				record = frappe.db.sql("""SELECT AP.`name`, AP.`posting_date`, AP.`employee`, TE.`full_name` FROM """+table+""" AP JOIN `tabEmployee` TE WHERE AP.`employee` = TE.`name` AND AP.`docstatus` = 0 AND (AP.`posting_date` BETWEEN %s AND %s) """, (getdate(self.from_date), getdate(self.to_date)), as_dict=True)

		entries = []
		for a in record:
			row = {
				"apptype": self.application_type,
				"application": a.name,
				"date": a.posting_date,
				"employee": a.employee,
				"employee_name": a.full_name,
				"action": "Approved"
			}
			entries.append(row);

		for d in entries:
			row = self.append('batch_table', {})
			row.update(d)

	def approve_applications(self):
		for b in self.get("batch_table"):
			if b.action == "Approved":
				application = frappe.get_doc(self.application_type, b.application)
				application.update({
					"workflow_state": "Approved",
					"approved_by" = frappe.session.user
					"approved_on" = nowdate()
				})
				application.save()
				application.submit()