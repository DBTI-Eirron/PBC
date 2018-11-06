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

	def set_header(self):
		header = "STANDARDS:"
		result = frappe.db.sql("""SELECT * FROM `tabTarget Standard`""",as_dict=True)
		for r in result:
			header += " " + r.rating + " - " + r.description + " ,"
		header = header[:-1] + "."
		self.header = header

	def validate(self):
		self.calculate_total()
		self.validate_total()
		self.validate_existing_appraisal()
		self.validate_rating()

		if not self.appraisal_goal:
			frappe.throw(_("Goals cannot be empty"))

	#self.rated_by = frappe.db.get_value("User", self.full_name, "full_name")

	def get_employee_name(self):
		self.appraisee_fullname = frappe.db.get_value("Employee", self.appraisee_name, "full_name")
		return self.appraisee_fullname

	def validate_existing_appraisal(self):
		chk = frappe.db.sql("""select name from `tabAppraisal` where appraisee=%s
			and (status='Submitted' or status='Completed')
			and ((from_date>=%s and from_date<=%s)
			or (to_date>=%s and to_date<=%s))""",
			(self.appraisee,self.from_date,self.to_date,self.from_date,self.to_date))
		if chk:
			frappe.throw(_("Appraisal {0} created for Appraisee {1} in the given date range").format(chk[0][0], self.appraisee_fullname))

	def validate_total(self):
		if self.total_score == 0:
			self.status = "Draft"
		else:
			self.status = "In Progress"

	def calculate_total(self):
		total, total_w, = 0, 0
		for d in self.appraisal_goal:
			if d.score:
				d.score_earned = flt(d.score) * flt(d.weightage) / 100
				total = total + d.score_earned
			total_w += flt(d.weightage)

		if d.score_earned > 4:
			frappe.throw(_("Score Earned can not be greater than 4"))

		if flt(total_w) != 100:
			frappe.throw(_("Total weightage assigned should be 100%. It is {0}").format(str(total_w) + "%"))

		self.total_score = total
	
	def validate_calculate_total(self):
		total, total_w, = 0, 0
		for d in self.appraisal_goal:
			if d.score:
				d.score_earned = flt(d.score) * flt(d.weightage) / 100
				total = total + d.score_earned
			total_w += flt(d.weightage)

		if d.score_earned > 4:
			frappe.throw(_("Score Earned can not be greater than 4"))

		if flt(total_w) != 100:
			frappe.throw(_("Total weightage assigned should be 100%. It is {0}").format(str(total_w) + "%"))

		if frappe.db.get_value("Employee", self.appraisee_name, "user_id") != \
				frappe.session.user and total == 0:
			frappe.throw(_("Total cannot be zero"))

		self.total_score = total


	def on_submit(self):
		self.validate_calculate_total()
		frappe.db.set(self, 'status', 'Submitted/Completed')
		frappe.db.set(self, 'date_completed', getdate(today()))

	def on_cancel(self):
		frappe.db.set(self, 'status', 'Cancelled')

	def get_performance_planning(self):
		kra = frappe.db.sql("""SELECT PP.type,PP.department,PP.appraisee,PP.appraisee_name,PP.planning_period,KI.key_result_area,KI.key_indicator,KI.weight FROM `tabTarget Setting` PP INNER JOIN `tabPerformance Planning KI` KI ON KI.parent = PP.name WHERE PP.name = %s ORDER BY KI.key_result_area ASC""",(self.target_setting),as_dict=True)
		entries = []
		for d in kra:
			self.appraisee_name = d.appraisee
			self.target_setting_period = d.planning_period
			self.appraisee_fullname = d.appraisee_name
			self.department = d.department
			self.type = d.type
			from_date,to_date = frappe.get_value("Target Setting Period",d.planning_period,["from_date","to_date"])
			self.from_date = from_date
			self.to_date = to_date
			row = {
				"key_result_area":d.key_result_area,
				"key_indicator":d.key_indicator,
				"weightage":d.weight
			}
			entries.append(row);
		for d in entries:
			row = self.append('appraisal_goal', {})
			row.update(d)


	def validate_rating(self):
		for d in self.appraisal_goal:
			desc = frappe.get_value("Target Standard",d.score,"description")
			d.equivalent_rating = desc
		if self.total_score < 1.75:
			self.equivalent_rating = "Did Not Meet Expectations"
		elif self.total_score < 2.49:
			self.equivalent_rating = "Barely Meet Expectations"
		elif self.total_score < 3.24:
			self.equivalent_rating = "Meets Expectations"
		elif self.total_score < 4:
			self.equivalent_rating = "Exceeds Expectations"