# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	result = get_result(filters)
	return columns, result

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)
	return result

def get_columns(filters):
	columns = [
		_("Employee") + ":Link/Employee:120",
		_("Employee Name") + "::200",
		_("Company") + ":Link/Company:200",
		_("Appraisal Template") + ":Link/Appraisal Template:120",
		_("Appraisal Type") + "::120",
		_("Appraisal Status") + "::120",
		_("Appraisal Dates") + ":Link/Appraisal Dates:120",
		_("Start Date") + "::120",
		_("End Date") + "::120",
		_("Date Created") + "::120",
		_("Due Date") + "::120",
		_("Date Completed") + "::120",
		_("Created by") + ":Link/User:120",
		_("Rated by") + ":Link/User:120",
		_("Goal") + "::120",
		_("Weightage") + "::120",
		_("Score Earned") + "::120",
		_("Total Score") + "::120",
	]

	return columns

def get_data(filters):

	entries = frappe.db.sql("""SELECT 
		TA.employee,
		TA.employee_name, 
		TA.company, 
		TA.appraisal_template,
		TA.appraisal_type,
		TA.status,
		TA.appraisal_dates,
		TA.start_date,
		TA.end_date,
		TA.date_created,
		TA.due_date,
		TA.date_completed,
		AG.kra,
		AG.weightage,
		AG.score_earned,
		TA.total_score,
		TA.created_by,
		TA.rated_by
	FROM tabAppraisal TA INNER JOIN `tabAppraisal Goal` AG ON TA.`name` = AG.parent WHERE TA.docstatus > 0 {conditions}  """.format(conditions=get_conditions(filters)), filters, as_dict=1)

	return entries

def get_conditions(filters):
	conditions = []

	if filters.get("employee"):
		emp_name = filters.get("employee")
		conditions.append("TA.employee LIKE '%%"+emp_name+"%%' ")

	if filters.get("appraisal_dates"):
		app_dates = filters.get("appraisal_dates")
		conditions.append("TA.appraisal_dates LIKE '%%"+app_dates+"%%' ")

	#if filters.get("start_date"):
	#	xstart_date = filters.get("start_date")
	#	conditions.append("TA.start_date LIKE '%%"+xstart_date+"%%' ")

	#if filters.get("end_date"):
	#	xend_date = filters.get("end_date")
	#	conditions.append("TA.end_date LIKE '%%"+xend_date+"%%' ")

	#if filters.get("date_completed"):
	#	xcom_date = filters.get("date_completed")
	#	conditions.append("TA.date_completed LIKE '%%"+xcom_date+"%%' ")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = [
			d.get("employee"),
			d.get("employee_name"),
			d.get("company"),
			d.get("appraisal_template"),
			d.get("appraisal_type"),
			d.get("status"),
			d.get("appraisal_dates"),
			d.get("start_date"),
			d.get("end_date"),
			d.get("date_created"),
			d.get("due_date"),
			d.get("date_completed"),
			d.get("created_by"),
			d.get("rated_by"),
			d.get("kra"),
			d.get("weightage"),
			d.get("score_earned"),
			d.get("total_score"),
		]

		result.append(row)

	return result