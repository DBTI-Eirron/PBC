# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, cstr, flt, nowdate
from frappe.model.document import Document

class EmployeeAccountability(Document):
	def validate_fields(self):
		if self.is_new() and self.employee_id:
			self.employee_id = None
			self.employee_name = None
			self.issued_by = None
			if self.type == 'Issuance':
				self.date_issued = nowdate()
				issued_name = frappe.db.sql("""SELECT `name`, full_name FROM `tabEmployee` WHERE `user_id` = %s LIMIT 1""",( frappe.session.user ), as_dict=1)
				if issued_name:
					self.issued_by = issued_name[0].name
					self.issued_by_name = issued_name[0].full_name
	
	def validate(self):
		self.validate_mandatory()
		if self.type == 'Issuance':
			self.date_issued = nowdate()
			issued_name = frappe.db.sql("""SELECT `name`, full_name FROM `tabEmployee` WHERE `user_id` = %s LIMIT 1""",( frappe.session.user ), as_dict=1)
			if issued_name:
				self.issued_by = issued_name[0].name
				self.issued_by_name = issued_name[0].full_name

	def on_submit(self):
		for d in self.return_table:
			frappe.db.sql("""UPDATE `tabAccountability Issuance Table` SET returned=1 WHERE `name` = %s""",( d.linked_doc ))
			frappe.db.commit()

	def validate_mandatory(self):
		if self.type == 'Issuance' and not self.issuance_table:
			frappe.throw(_("Fill in Issuance Table"))

		if self.type == 'Return' and not self.return_table:
			frappe.throw(_("You have no Issued Items to Return"))

	def set_issued_by(self):
		for d in self.issuance_table:
			issued_name = frappe.db.sql("""SELECT `name`, full_name FROM `tabEmployee` WHERE `user_id` = %s LIMIT 1""",( frappe.session.user ), as_dict=1)
			if issued_name:
				if d.issued_by == None:
					d.issued_by = cstr(issued_name[0].name)
					d.issued_by_name = cstr(issued_name[0].full_name)
			else:
				d.issued_by = None
				d.issued_by_name = None

	def get_issuance(self):
		if self.docstatus == 0:
			return_list = []
			issuance = frappe.db.sql("""SELECT IT.name, IT.item_name, IT.item_code, IT.quantity, EA.issued_by, EA.issued_by_name, EA.date_issued, IT.parent
			FROM `tabAccountability Issuance Table` IT INNER JOIN `tabEmployee Accountability` EA ON IT.`parent`=EA.`name`
			WHERE IT.returned = 0 AND EA.docstatus = 1 AND EA.company = %s AND EA.employee_id = %s GROUP BY IT.name """,( self.company, self.employee_id ), as_dict=1)

			for i in issuance:
				if i.parent not in return_list:
					ue = {
						"issuance": i.parent,
						"item_name": i.item_name,
						"item_code": i.item_code,
						"quantity": i.quantity,
						"issued_by": i.issued_by,
						"issued_by_name": i.issued_by_name,
						"date_issued": i.date_issued,
						"linked_doc": i.name,
					}
					row = self.append('return_table', {})
					row.update(ue)

			unique_emp = []
			unique_entries = []
			for d in self.return_table:
				if str(d.issuance+d.item_name+d.item_code) not in unique_emp:
					unique_emp.append(str(d.issuance+d.item_name+d.item_code));

					ins = {
						"issuance": d.issuance,
						"item_name": d.item_name,
						"item_code": d.item_code,
						"quantity": d.quantity,
						"issued_by": d.issued_by,
						"issued_by_name": d.issued_by_name,
						"date_issued": d.date_issued,
						"linked_doc": d.linked_doc,
					}	
					unique_entries.append(ins);

			self.set('return_table', [])
			for ue in unique_entries:
				row = self.append('return_table', {})
				row.update(ue)