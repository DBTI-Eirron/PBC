# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class TimekeepingSettings(Document):
	def validate(self):
		if self.enable_employee_approvers > 0:
			application = [ "Leave Approval Level", "Overtime Approval Level", "Official Business Approval Level", "Change Schedule Approval Level", "Excuse Tardiness Approval Level", "Undertime Approval Level", "DTR Problem Approval Level", "Compensatory Time Off Approval Level"]
			for a in application:
				workflow = frappe.get_doc("Workflow", a)
				workflow.update({
					"is_active": 1
				})
				workflow.save()

				app_list = [ "Leave Application", "Overtime Application", "Official Business Application", "Change Schedule Application", "Excuse Tardiness Application", "Undertime Application", "DTR Problem Application", "Compensatory Time Off"]
				for b in app_list:
					table_name = "`tab"+str(b)+"`"
					frappe.db.sql(""" UPDATE """+str(table_name)+""" SET docstatus=1 WHERE workflow_state="Pending" """)
					frappe.db.commit()
		else:
			application = [ "Leave Approval", "Overtime Approval", "Official Business Approval", "Change Schedule Approval", "Excuse Tardiness Approval", "Undertime Approval", "DTR Problem Approval", "Compensatory Time Off Approval"]
			for a in application:
				workflow = frappe.get_doc("Workflow", a)
				workflow.update({
					"is_active": 1
				})
				workflow.save()

			app_list = [ "Leave Application", "Overtime Application", "Official Business Application", "Change Schedule Application", "Excuse Tardiness Application", "Undertime Application", "DTR Problem Application", "Compensatory Time Off"]
			for b in app_list:
				table_name = "`tab"+str(b)+"`"
				frappe.db.sql(""" UPDATE """+str(table_name)+""" SET docstatus=0 WHERE workflow_state="Pending" """)
				frappe.db.commit()