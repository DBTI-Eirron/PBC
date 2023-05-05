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
		record = self.get_data()

		record_list = []
		for a in record:
			record_list.append(a['application'])

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
				entries.append(row)

		self.set('batch_table', [])
		for d in entries:
			row = self.append('batch_table', {})
			row.update(d)

	def on_submit(self):
		self.validate_entires()
		self.approve_applications()

	def map_applications_on_table(self):
		self.set('batch_table', [])
		record = self.get_data()

		entries = []
		for a in record:
			a['action'] = 'Approved'
			entries.append(a)

		for d in entries:
			row = self.append('batch_table', {})
			row.update(d)

	def approve_applications(self):
		enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
		table = "`tab"+self.application_type+"`"

		for b in self.get("batch_table"):
			if b.action == "Approved":
				if enable_employee_approvers == 0:
					application = frappe.get_doc(self.application_type, b.application)
					application.update({
						"workflow_state": "Approved",
						"approved_by": frappe.session.user,
						"approved_on": nowdate(),
					})
					application.submit()
				else:
					application = frappe.get_doc(self.application_type, b.application)
					app_hist = ""
					if application.approval_history:
						app_hist = application.approval_history

					application.update({
						"workflow_state": "Approved",
						"approved_by": frappe.session.user,
						"approved_on": nowdate(),
						"approval_history": app_hist+cstr("Batch Approved: "),
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

	def get_filter_date(self):
		appfilterdate = "posting_date"

		if self.based_on == "Target Date":
			if self.application_type in ["Overtime Application", "Official Business Application", "Undertime Application", 
				"Change Schedule Application", "DTR Problem Application"]:
				appfilterdate = "target_date"

			if self.application_type in ["Leave Application"]:
				appfilterdate = "leave_date"

			if self.application_type in ["Excuse Tardiness Application"]:
				appfilterdate = "date"

			if self.application_type in ["Compensatory Time Off"]:
				appfilterdate = "from_date"

		return appfilterdate

	def get_data(self):
		final_result = []
		result = None
		application_list = [self.application_type]
		cur_user = frappe.session.user
		application_type = self.application_type
		appfilterdate = self.get_filter_date()
		ta_dict = None

		if self.application_type in ["Compensatory Time Off"]:
			application_list = ["Compensatory Time Off (Use)", "Compensatory Time Off (File)"]

		for app in application_list:
			appfilters = [
				["workflow_state", "in", ["Pending", "Approval in Progress"]],
				[appfilterdate, ">=", str(getdate(self.from_date))],
				[appfilterdate, "<=", str(getdate(self.to_date))],
				["company", "=", self.company]
			]

			if app == "Compensatory Time Off (File)":
				appfilters.append(["type", "in", "File"])
				app = "Compensatory Time Off"

			if app == "Compensatory Time Off (Use)":
				appfilters.append(["type", "in", "Use"])
				app = "Compensatory Time Off"

			if self.employee:
				appfilters.append(["employee", "in", self.employee])

			if app == "Timelogs Application":
				included_ta = []
				ta_dict = {}
				ta_result = frappe.db.sql(""" SELECT TA.`parent`, TA.`target_date` FROM `tabTimelogs Application Table` TA JOIN `tabTimelogs Application` T ON TA.`parent` = T.`name` 
					WHERE T.`workflow_state` IN ('Pending', 'Approval in Progress') """, as_dict=1)

				for tar in ta_result:
					if tar.parent not in ta_dict:
						ta_dict[tar.parent] = []
					ta_dict[tar.parent].append(tar.target_date)

				if ta_dict:
					for ta in ta_dict:
						if self.based_on == "Target Date":
							if (getdate(self.from_date) <= min(ta_dict[ta]) <= getdate(self.to_date)) and (getdate(self.from_date) <= max(ta_dict[ta]) <= getdate(self.to_date)):
								included_ta.append(ta)
						else:
							included_ta.append(ta)

				appfilters.append(["name", "in", included_ta])

			if not any(elem in ["Administrator", "Admin Approver"] for elem in frappe.get_roles(cur_user)):
				result = frappe.get_list(app, filters=appfilters, fields=['name'])
			else:
				result = frappe.get_all(app, filters=appfilters)

			if result:
				for res in result:
					#init row
					row = {}
					row["apptype"] = None
					row["application"] = None
					row["date"] = None
					row["from_date"] = None
					row["to_date"] = None
					row["total_hours"] = None
					row["employee"] = None
					row["employee_name"] = None

					#Define Row
					row["apptype"] = application_type
					row["application"] = res['name']
					doc = frappe.get_doc(application_type, res['name'])
					row["employee"] = doc.employee
					row["date"] = doc.posting_date

					if application_type in ["Leave Application"]:
						row["from_date"] = doc.from_date
						row["to_date"] = doc.to_date

					if application_type in ["Overtime Application"]:
						row["from_date"] = doc.from_date
						row["to_date"] = doc.to_date
						row["total_hours"] = doc.total_hrs

					if application_type in ["Official Business Application"]:
						row["from_date"] = doc.from_date
						row["to_date"] = doc.to_date
						row["total_hours"] = doc.total_hrs

					if application_type in ["Change Schedule Application"]:
						row["from_date"] = doc.from_date
						row["to_date"] = doc.to_date

					if application_type in ["Excuse Tardiness Application"]:
						row["from_date"] = doc.date
						row["to_date"] = doc.date

					if application_type in ["Undertime Application"]:
						row["from_date"] = doc.from_date
						row["to_date"] = doc.to_date
						row["total_hours"] = doc.total_hrs

					if application_type in ["DTR Problem Application"]:
						row["from_date"] = doc.target_date
						row["to_date"] = doc.target_date

					if application_type in ["Compensatory Time Off"]:
						row["from_date"] = doc.from_date
						row["to_date"] = doc.to_date
						row["total_hours"] = doc.total_hours

					if application_type in ["Timelogs Application"]:
						if ta_dict:
							row["from_date"] = min(ta_dict[res['name']])
							row["to_date"] = max(ta_dict[res['name']])

					row["employee_name"] = frappe.db.get_value("Employee", row["employee"], ["full_name"])
					to_append = 1

					if not any(elem in ["Administrator", "Admin Approver"] for elem in frappe.get_roles(cur_user)):
						if frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers'):
							to_append = 0
							req_level = int(doc.last_approval_level)+1
							approver_level = frappe.db.sql(""" SELECT IFNULL(MAX(EA.`level`), 0) as `level` FROM `tabEmployee Approvers` EA JOIN `tabEmployee` TE ON EA.`approver` = TE.`name` 
								WHERE EA.parenttype = "Employee" AND (EA.application = %s OR EA.application = "All") AND EA.parent = %s AND TE.user_id = %s AND EA.`level` = %s """,(doc.doctype, doc.employee, frappe.session.user, int(req_level)), as_dict=1)
							if approver_level:
								if str(req_level) == str(approver_level[0].level):
									to_append = 1

					if to_append:
						final_result.append(row)

		return final_result