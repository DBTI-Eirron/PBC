# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class TimekeepingSettings(Document):
	def validate(self):
		self.validate_employee_approvers()
		self.validate_section_cto()

	#Enable Employee Approvers
	def validate_employee_approvers(self):
		app_list = [ "Leave Application", "Overtime Application", "Official Business Application", "Change Schedule Application", "Excuse Tardiness Application", "Undertime Application", "DTR Problem Application", "Compensatory Time Off", "Timelogs Application"]
		if self.enable_employee_approvers > 0:
			application = [ "Leave Approval Level", "Overtime Approval Level", "Official Business Approval Level", "Change Schedule Approval Level", "Excuse Tardiness Approval Level", 
				"Undertime Approval Level", "DTR Problem Approval Level", "Compensatory Time Off Approval Level", "Timelogs Application Approval Level"]
			for a in application:
				workflow = frappe.get_doc("Workflow", a)
				workflow.update({
					"is_active": 1
				})
				workflow.save()

				for b in app_list:
					table_name = "`tab"+str(b)+"`"
					frappe.db.sql(""" UPDATE """+str(table_name)+""" SET docstatus=1 WHERE workflow_state="Pending" """)
					frappe.db.commit()
		else:
			application = [ "Leave Approval", "Overtime Approval", "Official Business Approval", "Change Schedule Approval", "Excuse Tardiness Approval", "Undertime Approval", 
				"DTR Problem Approval", "Compensatory Time Off Approval", "Timelogs Application Approval"]
			for a in application:
				workflow = frappe.get_doc("Workflow", a)
				workflow.update({
					"is_active": 1
				})
				workflow.save()

			for b in app_list:
				table_name = "`tab"+str(b)+"`"
				frappe.db.sql(""" UPDATE """+str(table_name)+""" SET docstatus=0 WHERE workflow_state="Pending" """)
				frappe.db.commit()

	#Section Compensatory Time Off
	def validate_section_cto(self):
		if self.cto_max_filing:
			included_entry = []
			table_entry = []
			for cto in self.cto_max_filing:
				if cto.frequency not in included_entry:
					table_entry.append({
						"frequency": cto.frequency,
						"max_count": cto.max_count,
					})
					included_entry.append(cto.frequency)

			self.cto_max_filing = []
			for ent in table_entry:
				row = self.append('cto_max_filing', {
					"frequency": ent['frequency'],
					"max_count": ent['max_count'],
				})

	def convert_credits(self):
		cto = frappe.db.sql("""SELECT * FROM `tabCompensatory Time Off` """, as_dict=1)
		for d in cto:
			if d['type'] == 'File':
				pass
			if d['type'] == 'Use':
				pass