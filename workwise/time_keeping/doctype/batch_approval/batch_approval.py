# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import time, datetime, timedelta
from frappe.utils import cstr, cint, flt, nowdate, add_days, getdate, fmt_money, now_datetime
from frappe import _, msgprint
from frappe.model.document import Document

class BatchApproval(Document):
	def clear_employee(self):
		if self.is_new() and self.employee:
			self.employee = None

	def validate(self):
		self.validate_entires()

	def validate_entires(self):
		record = self.sql_query()

		record_list = []
		for a in record:
			record_list.append(a.name);

		entries = []
		for b in self.get("batch_table"):
			if b.application in record_list:
				row = {
					"apptype": b.apptype,
					"application": b.application,
					"date": b.date,
					"from_date": b.from_date,
					"to_date": b.to_date,
					"total_hours": b.total_hours,
					"employee": b.employee,
					"employee_name": b.employee_name,
					"action": b.action
				}
				entries.append(row);

		self.set('batch_table', [])
		for d in entries:
			row = self.append('batch_table', {})
			row.update(d)

	def on_submit(self):
		self.validate_entires()
		self.approve_applications()

	def map_applications_on_table(self):
		self.set('batch_table', [])
		record = self.sql_query()

		entries = []
		for a in record:
			total_hours = ""
			from_date = ""
			to_date = ""

			if self.application_type in ["Overtime Application", "Official Business Application", "Undertime Application"]:
				total_hours = flt(a.total_hrs, 2)
			if self.application_type in ["Overtime Application", "Official Business Application", "Leave Application", "Change Schedule Application"]:
				from_date = a.from_date
				to_date = a.to_date
			if self.application_type == "Undertime Application":
				from_date = a.from_date
				to_date = a.from_date
			if self.application_type == "Excuse Tardiness Application":
				from_date = a.date
				to_date = a.date
			if self.application_type == "DTR Problem Application":
				from_date = a.target_date
				to_date = a.target_date
			if self.application_type == "Compensatory Time Off":
				if a.type == "File":
					from_date = a.date
					to_date = a.date
					total_hours = flt(a.total_hours, 2)
				else:
					from_date = a.use_date
					to_date = a.use_date
					total_hours = flt(a.use_total_hours, 2)

			row = {
				"apptype": self.application_type,
				"application": a.name,
				"date": a.posting_date,
				"from_date": from_date,
				"to_date": to_date,
				"total_hours": total_hours,
				"employee": a.employee,
				"employee_name": a.full_name,
				"action": "Approved"
			}
			entries.append(row);

		for d in entries:
			row = self.append('batch_table', {})
			row.update(d)

	def approve_applications(self):
		table = "`tab"+self.application_type+"`"
		for b in self.get("batch_table"):
			if b.action == "Approved":
				enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
				if enable_employee_approvers == 0:
					#approval_history = ""
					#approver_level = frappe.db.sql(""" SELECT IFNULL(MAX(EA.`level`), 0) as `level` FROM `tabEmployee Approvers` EA JOIN `tabEmployee` TE ON EA.`approver` = TE.`name` WHERE EA.parenttype = "Employee" AND (EA.application = %s OR EA.application = "All") AND EA.parent = %s AND TE.user_id = %s """,(self.application_type, b.employee, frappe.session.user), as_dict=True)
					#highest_level = frappe.db.sql(""" SELECT IFNULL(MAX(`level`), 0) as level FROM `tabEmployee Approvers` WHERE parenttype = "Employee" AND (`application` = %s OR `application` = "All") AND parent = %s """,(self.application_type, b.employee), as_dict=True)	
					#if approver_level[0].level == highest_level[0].level:
					#	if approval_history is not None:
					#		approval_history = frappe.db.get_value(self.application_type, b.application, "approval_history")
					#	else:
					#		approval_history = ""
					#	approval_history = str(approval_history)+"Level "+str(highest_level[0].level)+": "+str(frappe.session.user)+" approved on "+str(now_datetime().strftime('%Y-%m-%d %H:%M:%S'))+"\n"
					#	suc = frappe.db.sql("""UPDATE """+table+""" SET approval_history = %s, last_approval_level = %s, workflow_state = "Approved", approved_by = %s, approved_on = %s WHERE `name` = %s """, (approval_history, highest_level[0].level, frappe.session.user, nowdate(), b.application))
					#	frappe.db.commit()
					#	if suc:
					#		frappe.msgprint(_("<b>{0}: {1}</b><hr> Approval Successful").format(self.application_type, b.application))
					#else:
					#	if approval_history is not None:
					#		approval_history = frappe.db.get_value(self.application_type, b.application, "approval_history")
					#	else:
					#		approval_history = ""
					#	approval_history = str(approval_history)+"Level "+str(approver_level[0].level)+": "+str(frappe.session.user)+" approved on "+str(now_datetime().strftime('%Y-%m-%d %H:%M:%S'))+"\n"
					#	suc = frappe.db.sql("""UPDATE """+table+""" SET approval_history = %s, last_approval_level = %s, workflow_state = "Approval in Progress" WHERE `name` = %s """, (approval_history, approver_level[0].level, b.application))
					#	frappe.db.commit()
					#	if suc:
					#		frappe.msgprint(_("<b>{0}: {1}</b><hr> Approval Successful").format(self.application_type, b.application))
					application = frappe.get_doc(self.application_type, b.application)
					application.submit()
				else:
					application = frappe.get_doc(self.application_type, b.application)
					#approval_history = ""
					#if application.approval_history is not None:
					#	approval_history = application.approval_history
					#approval_history = str(approval_history)+"Level "+str(application.last_approval_level)+": "+str(frappe.session.user)+" batch approved on "+str(now_datetime().strftime('%Y-%m-%d %H:%M:%S'))+"\n"

					application.update({
						"workflow_state": "Approved",
						"approved_by": frappe.session.user,
						"approved_on": nowdate(),
						"approval_history": "Batch Approved: ",
					})
					application.submit()
			if b.action == "Rejected":
				frappe.db.sql("""UPDATE """+table+""" SET docstatus = 2, workflow_state = "Rejected" WHERE `name` = %s """, (b.application))
				frappe.db.commit()

	def sql_select_filters(self):
		conditions = []
		if self.employee:
			conditions.append("TE.`name`=%(employee)s")

		return "AND {}".format(" AND ".join(conditions)) if conditions else ""

	def sql_query(self):
		cur_user = frappe.session.user
		table = "`tab"+self.application_type+"`"
		additional_fields = ""
		filter_date = "AP.`posting_date`"

		if self.application_type in ["Overtime Application", "Official Business Application", "Undertime Application"]:
			additional_fields += ", AP.total_hrs"
		if self.application_type in ["Overtime Application", "Official Business Application", "Leave Application", "Change Schedule Application"]:
			additional_fields += ", AP.from_date, AP.to_date"
			if self.based_on == "Target Date":
				filter_date = "AP.from_date"
		if self.application_type == "Undertime Application":
			additional_fields += ", AP.from_date"
			if self.based_on == "Target Date":	
				filter_date = "AP.from_date"
		if self.application_type == "Excuse Tardiness Application":
			additional_fields += ", AP.date"
			if self.based_on == "Target Date":	
				filter_date = "AP.date"
		if self.application_type in ["DTR Problem Application"]:
			additional_fields += ", AP.target_date"
			if self.based_on == "Target Date":	
				filter_date = "AP.target_date"
		if self.application_type == "Compensatory Time Off":
			additional_fields += ", AP.`date`, AP.use_date, AP.`type`, AP.use_total_hours, AP.total_hours"
			if self.based_on == "Target Date":	
				filter_date = "AP.`date` or AP.use_date"

		if not "Administrator" in frappe.get_roles(cur_user):
			enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
			if enable_employee_approvers > 0:
				record = frappe.db.sql(""" SELECT DISTINCT AP.`name`, AP.`posting_date`, AP.`employee`, TE.`full_name` """+additional_fields+""" 
						FROM """+table+""" AP JOIN `tabEmployee` TE ON AP.`employee` = TE.`name` 
						WHERE ( AP.`workflow_state` = "Pending" OR AP.`workflow_state` = "Approval in Progress" ) 
						AND ( """+filter_date+""" BETWEEN %(from_date)s AND %(to_date)s ) 
						AND TE.`name` IN ( SELECT `for_value` FROM `tabUser Permission` WHERE `allow` = "Employee" AND `user` = %(cur_user)s ) {conditions} 
						AND TE.company = %(company)s
						AND AP.`employee` IN (SELECT DISTINCT AE.`parent` FROM `tabEmployee` ET INNER JOIN `tabEmployee Approvers` AE ON ET.`name`=AE.`approver` WHERE ET.user_id = %(cur_user)s AND (AE.`application`=%(application)s OR AE.`application`="All") AND AE.`level` = AP.`last_approval_level`+1)
					""".format(conditions=self.sql_select_filters()),{ 
						"company": self.company,
						"employee": self.employee,
						"from_date": getdate(self.from_date),
						"to_date": getdate(self.to_date),
						"application": self.application_type,
						"cur_user": cur_user,
				}, as_dict=True)
			else:
				record = frappe.db.sql(""" SELECT DISTINCT AP.`name`, AP.`posting_date`, AP.`employee`, TE.`full_name`"""+additional_fields+""" 
						FROM """+table+""" AP JOIN `tabEmployee` TE ON AP.`employee` = TE.`name` 
						WHERE (AP.`workflow_state` = "Pending" OR AP.`workflow_state` = "Approval in Progress")
						AND ("""+filter_date+""" BETWEEN %(from_date)s AND %(to_date)s) 
						{conditions} 
						AND TE.company = %(company)s 
					""".format(conditions=self.sql_select_filters()),{ 
						"company": self.company,
						"employee": self.employee,
						"from_date": getdate(self.from_date),
						"to_date": getdate(self.to_date),
						"cur_user": cur_user,
					}, as_dict=True)
		else:
			record = frappe.db.sql("""SELECT AP.`name`, AP.`posting_date`, AP.`employee`, TE.`full_name`"""+additional_fields+""" 
					FROM """+table+""" AP JOIN `tabEmployee` TE 
					WHERE AP.`employee` = TE.`name` 
					AND (AP.`workflow_state` = "Pending" OR AP.`workflow_state` = "Approval in Progress")
					AND ("""+filter_date+""" BETWEEN %(from_date)s AND %(to_date)s) 
					{conditions}
					AND TE.company = %(company)s 
				""".format(conditions=self.sql_select_filters()),{ 
					"company": self.company,
					"employee": self.employee,
					"from_date": getdate(self.from_date),
					"to_date": getdate(self.to_date),
				}, as_dict=True)

		return record


