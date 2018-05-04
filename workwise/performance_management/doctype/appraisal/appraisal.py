# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe 
from frappe.utils import flt, getdate, today
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

class Appraisal(Document):
	def validate(self):
		self.calculate_total()
		self.validate_total()
		self.validate_existing_appraisal()

		if not self.goals:
			frappe.throw(_("Goals cannot be empty"))

	#self.rated_by = frappe.db.get_value("User", self.full_name, "full_name")

	def get_employee_name(self):
		self.employee_name = frappe.db.get_value("Employee", self.employee, "full_name")
		return self.employee_name

	def validate_existing_appraisal(self):
		chk = frappe.db.sql("""select name from `tabAppraisal` where employee=%s
			and (status='Submitted' or status='Completed')
			and ((start_date>=%s and start_date<=%s)
			or (end_date>=%s and end_date<=%s))""",
			(self.employee,self.start_date,self.end_date,self.start_date,self.end_date))
		if chk:
			frappe.throw(_("Appraisal {0} created for Employee {1} in the given date range").format(chk[0][0], self.employee_name))

	def validate_total(self):
		if self.total_score == 0:
			self.status = "Draft"
		else:
			self.status = "In Progress"

	def calculate_total(self):
		total, total_w, = 0, 0
		for d in self.goals:
			if d.score:
				d.score_earned = flt(d.score) * flt(d.weightage) / 100
				total = total + d.score_earned
			total_w += flt(d.weightage)

		if d.score_earned > 5:
			frappe.throw(_("Score Earned can not be greater than 5"))

		if flt(total_w) != 100:
			frappe.throw(_("Total weightage assigned should be 100%. It is {0}").format(str(total_w) + "%"))

		self.total_score = total
	
	def validate_calculate_total(self):
		total, total_w, = 0, 0
		for d in self.goals:
			if d.score:
				d.score_earned = flt(d.score) * flt(d.weightage) / 100
				total = total + d.score_earned
			total_w += flt(d.weightage)

		if d.score_earned > 5:
			frappe.throw(_("Score Earned can not be greater than 5"))

		if flt(total_w) != 100:
			frappe.throw(_("Total weightage assigned should be 100%. It is {0}").format(str(total_w) + "%"))

		if frappe.db.get_value("Employee", self.employee, "user_id") != \
				frappe.session.user and total == 0:
			frappe.throw(_("Total cannot be zero"))

		self.total_score = total


	def on_submit(self):
		self.validate_calculate_total()
		frappe.db.set(self, 'status', 'Submitted/Completed')
		frappe.db.set(self, 'date_completed', getdate(today()))

	def on_cancel(self):
		frappe.db.set(self, 'status', 'Cancelled')

	def get_appraisal_template_goal(self):
		self.set('appraisal_template_goal', [])
		entries = [];
		goal = frappe.db.sql("""select kra, weightage from `tabAppraisal Template Goal` 
			where parent=%s and docstatus=0 """,(self.appraisal_template), as_dict=True)

		for i in goal:
		    info = {

		        "kra": i.kra,
		        "weightage": i.weightage,
		    }

		    entries.append(info)
			
		for d in entries:
			row = self.append('goals', {})
			row.update(d)