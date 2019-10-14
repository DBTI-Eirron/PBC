# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr
from frappe import _
from frappe.model.document import Document

class TargetSettings(Document):
	def validate(self):
		self.validate_weight()
		self.set_header()
		# self.validate_kra()

	def on_submit(self):
		if self.workflow_state == "Approved":
			for tar in self.target_employees:
				header = {
					"title":cstr(self.planning_title) +", " +cstr(tar.employee),
					"target_setting":self.name,
					"appraisee":tar.employee,
					"appraisee_name":tar.employee_name,
					"job_title":tar.job_title,
					"date_joined":tar.date_hired,
					"company":tar.company,
					"department":tar.department,
					"from_date":self.from_date,
					"to_date":self.to_date
				}
				doc = frappe.new_doc("Evaluation")
				doc.update(header)
				doc.insert()

				idx = 0
				for key in self.key_indicator:
					idx += 1
					frappe.db.sql("INSERT INTO `tabAppraisal Goal` (name,parent,key_indicator,weightage,idx,parentfield,parenttype) VALUES ('"+cstr(key.key_indicator)+"-"+cstr(self.planning_title)+"-"+cstr(tar.employee)+"','"+cstr(self.planning_title) +", " +cstr(tar.employee)+"','"+cstr(key.key_indicator)+"','"+cstr(key.weight)+"','"+cstr(idx)+"','appraisal_goal','Evaluation')")

	def validate_weight(self):
		total_w = 0.0
		for d in self.key_indicator:
			total_w += float(d.weight)
		if total_w != 100:
			frappe.throw(_("Total weightage assigned should be 100%. It is {0}").format(str(total_w) + "%"))

	def set_header(self):
		header = "STANDARDS:"
		result = frappe.db.sql("""SELECT rating_equivalent,rate_to FROM `tabRating Classification` ORDER BY rate_to ASC""",as_dict=True)
		for r in result:
			header += " " + str(int(r.rate_to)) + " - " + str(r.rating_equivalent) + " ,"
		header = header[:-1] + "."
		self.header = header

	def get_employees(self):
		employees = frappe.db.sql("""SELECT EM.name,EM.full_name,EM.position_title,EM.date_hired,EM.company,EM.department FROM `tabEmployee` EM WHERE EM.is_active = 1"""+self.add_filters(),as_dict=True)

		entries	= []
		for d in employees:
			row = {
				"employee": d.name,
				"employee_name": d.full_name,
				"job_title":d.position_title,
				"date_hired":d.date_hired,
				"company":d.company,
				"department":d.department
			}
			entries.append(row);

		for d in entries:
			row = self.append('target_employees', {})
			row.update(d)

	def add_filters(self):
		filt = ""
		if self.employee:
			filt += " AND EM.`name` = '"+self.employee+"'"
		if self.company:
			filt += " AND EM.company = '"+self.company+"'"
		if self.location:
			filt += " AND EM.location = '"+self.location+"'"
		if self.department:
			filt += " AND EM.department = '"+self.department+"'"
		return filt	

	# def validate_kra(self):
	# 	total = total_ki = 0 
	# 	for d in self.key_result_area:
	# 		total += 1
	# 		for x in self.key_indicator:
	# 			if x.key_result_area == d.key_result_area:
	# 				total_ki += 1
	# 		if total_ki > 3:
	# 			frappe.throw(_("Key Indicator per Result Area must not be greater than 3"))
	# 	if total > 4:
	# 		frappe.throw(_("Key Result Area must not be greater than 4"))

